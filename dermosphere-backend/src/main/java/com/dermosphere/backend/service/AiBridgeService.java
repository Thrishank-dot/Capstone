package com.dermosphere.backend.service;

import com.dermosphere.backend.dto.AiResponseDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.server.ResponseStatusException;

import reactor.core.publisher.Mono;

@Service
public class AiBridgeService {

    @Value("${ai.microservice.url:http://127.0.0.1:8000/api/v1/triage/predict}")
    private String aiServiceUrl;

    private final WebClient webClient;
    

    public AiBridgeService(WebClient webClient) {
        this.webClient = webClient;
    }

    public Mono<AiResponseDto> processImageInferenceReactive(MultipartFile file) {
        return processImageInferenceReactive(file, "0.0", "0", "0");
    }

    public Mono<AiResponseDto> processImageInferenceReactive(
            MultipartFile file,
            String ageScaled,
            String sexEncoded,
            String anatomyEncoded
    ) {
        try {
            byte[] bytes = file.getBytes();
            
            // Explicitly override contentLength() to prevent Netty payload corruption
            ByteArrayResource fileResource = new ByteArrayResource(bytes) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename() != null ? file.getOriginalFilename() : "lesion_image.jpg";
                }

                @Override
                public long contentLength() {
                    return bytes.length;
                }
            };

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", fileResource);
            body.add("age_scaled", ageScaled != null ? ageScaled : "0.0");
            body.add("sex_encoded", sexEncoded != null ? sexEncoded : "0");
            body.add("anatomy_encoded", anatomyEncoded != null ? anatomyEncoded : "0");

            return webClient
                    .post()
                    .uri(aiServiceUrl)
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .bodyValue(body)
                    .exchangeToMono(response -> {
                        if (response.statusCode().is2xxSuccessful()) {
                            return response.bodyToMono(AiResponseDto.class);
                        }
                        
                        // Handle 400 Bad Request (e.g., blurry image quality checks) gracefully
                        if (response.statusCode().is4xxClientError()) {
                            return response.bodyToMono(String.class)
                                    .defaultIfEmpty("Invalid input parameters or blurry image.")
                                    .flatMap(errorBody -> Mono.error(
                                            new ResponseStatusException(HttpStatus.BAD_REQUEST, errorBody)
                                    ));
                        }

                        // Handle 500 Internal Server Errors from FastAPI
                        return response.bodyToMono(String.class)
                                .defaultIfEmpty("Unknown AI service error")
                                .flatMap(errorBody -> Mono.error(
                                        new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "AI Service Error: " + errorBody)
                                ));
                    });
        } catch (Exception e) {
            return Mono.error(
                    new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Failed to prepare AI request: " + e.getMessage(), e)
            );
        }
    }
}