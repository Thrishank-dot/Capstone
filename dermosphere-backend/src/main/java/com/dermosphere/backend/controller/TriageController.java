package com.dermosphere.backend.controller;

import com.dermosphere.backend.entity.ScanRecord;
import com.dermosphere.backend.repository.ScanRecordRepository;
import com.dermosphere.backend.service.AiBridgeService;

import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import reactor.core.publisher.Mono;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/triage")
public class TriageController {

    private final AiBridgeService aiBridgeService;
    private final ScanRecordRepository scanRecordRepository;
    private final String localUploadStorage;

    public TriageController(
            AiBridgeService aiBridgeService,
            ScanRecordRepository scanRecordRepository
    ) {
        this.aiBridgeService = aiBridgeService;
        this.scanRecordRepository = scanRecordRepository;

        File currentDir = new File(System.getProperty("user.dir"));

        File workspaceRoot =
                currentDir.getParentFile() != null
                        ? currentDir.getParentFile()
                        : currentDir;

        File targetUploadDir = new File(
                workspaceRoot,
                "dermosphere-ai-service/static/uploads/"
        );

        this.localUploadStorage =
                targetUploadDir.getAbsolutePath() + File.separator;

        if (!targetUploadDir.exists()) {
            targetUploadDir.mkdirs();
        }

        System.out.println(
                "[TRIAGE] Upload directory: " + this.localUploadStorage
        );
    }


    @PostMapping("/upload")
    @CacheEvict(value = "triageQueue", allEntries = true)
    public Mono<ResponseEntity<?>> uploadLesionImage(

            @RequestParam("file") MultipartFile file,

            @RequestParam(
                    value = "patient_id",
                    defaultValue = "1"
            ) Long patientId
    ) {

        if (file == null || file.isEmpty()) {

            return Mono.just(
                    ResponseEntity
                            .badRequest()
                            .body(
                                    Map.of(
                                            "status", "error",
                                            "message", "No image file uploaded."
                                    )
                            )
            );
        }


        String originalFilename = file.getOriginalFilename();

        if (originalFilename == null || originalFilename.isBlank()) {
            originalFilename = "uploaded_image.jpg";
        }


        String safeFilename =
                originalFilename.replaceAll(
                        "[^a-zA-Z0-9._-]",
                        "_"
                );


        String destinationPath =
                localUploadStorage
                        + System.currentTimeMillis()
                        + "_"
                        + safeFilename;


        try {

            File destinationFile = new File(destinationPath);

            Files.copy(
                    file.getInputStream(),
                    destinationFile.toPath(),
                    StandardCopyOption.REPLACE_EXISTING
            );

            System.out.println(
                    "[TRIAGE] Image saved successfully: "
                            + destinationPath
            );

        } catch (IOException e) {

            System.err.println(
                    "[TRIAGE ERROR] File persistence failed: "
                            + e.getMessage()
            );

            return Mono.just(
                    ResponseEntity
                            .internalServerError()
                            .body(
                                    Map.of(
                                            "status", "error",
                                            "message",
                                            "File persistence failed: "
                                                    + e.getMessage()
                                    )
                            )
            );
        }


        return aiBridgeService
                .processImageInferenceReactive(file)

                .<ResponseEntity<?>>map(aiResult -> {

                    ScanRecord record = new ScanRecord();

                    record.setPatientId(patientId);

                    record.setOriginalFilename(
                            file.getOriginalFilename()
                    );

                    record.setStoredFilePath(
                            destinationPath
                    );

                    record.setPredictedClass(
                            aiResult.getPrediction()
                    );

                    record.setConfidenceScore(
                            aiResult.getConfidence()
                    );

                    record.setTriageTier(
                            aiResult.getTriage_tier()
                    );

                    record.setHeatmapPath(
                            aiResult.getHeatmap_path()
                    );


                    ScanRecord savedRecord =
                            scanRecordRepository.save(record);


                    System.out.println(
                            "[TRIAGE SUCCESS] Prediction: "
                                    + savedRecord.getPredictedClass()
                    );


                    return ResponseEntity.ok(savedRecord);
                })

                .onErrorResume(error -> {

                    System.err.println(
                            "[TRIAGE ERROR] AI inference failed"
                    );

                    error.printStackTrace();


                    String errorMessage =
                            error.getMessage() != null
                                    ? error.getMessage()
                                    : "Unknown AI inference error";


                    return Mono.just(
                            ResponseEntity
                                    .internalServerError()
                                    .body(
                                            Map.of(
                                                    "status", "error",
                                                    "message", errorMessage
                                            )
                                    )
                    );
                });
    }


    @GetMapping("/queue")
    @Cacheable(value = "triageQueue")
    public ResponseEntity<List<ScanRecord>> getClinicalTriageQueue() {

        return ResponseEntity.ok(
                scanRecordRepository
                        .findAllByOrderByTriageTierDescScannedAtDesc()
        );
    }


    @PatchMapping("/feedback/{id}")
    @CacheEvict(value = "triageQueue", allEntries = true)
    public ResponseEntity<?> submitDoctorFeedback(

            @PathVariable Long id,

            @RequestBody Map<String, String> body
    ) {

        ScanRecord record =
                scanRecordRepository
                        .findById(id)
                        .orElseThrow(
                                () -> new RuntimeException(
                                        "Target Scan Record missing."
                                )
                        );


        String feedbackValue = body.get("feedback");


        if (feedbackValue == null || feedbackValue.isBlank()) {

            return ResponseEntity
                    .badRequest()
                    .body(
                            Map.of(
                                    "status", "error",
                                    "message", "Feedback value is required."
                            )
                    );
        }


        if (feedbackValue.equalsIgnoreCase("AGREE")) {

            record.setUpvotes(
                    record.getUpvotes() + 1
            );

        } else if (feedbackValue.equalsIgnoreCase("DISAGREE")) {

            record.setDownvotes(
                    record.getDownvotes() + 1
            );

        } else {

            return ResponseEntity
                    .badRequest()
                    .body(
                            Map.of(
                                    "status", "error",
                                    "message",
                                    "Feedback must be AGREE or DISAGREE."
                            )
                    );
        }


        record.setDoctorFeedback(
                feedbackValue.toUpperCase()
        );


        scanRecordRepository.save(record);


        return ResponseEntity.ok(
                Map.of(
                        "status", "success",
                        "message", "Engagement tracked. Feed updated."
                )
        );
    }
}