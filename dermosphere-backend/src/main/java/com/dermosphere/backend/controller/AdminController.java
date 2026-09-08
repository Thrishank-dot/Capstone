package com.dermosphere.backend.controller;

import com.dermosphere.backend.repository.ScanRecordRepository;
import com.dermosphere.backend.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin")
public class AdminController {

    private final UserRepository userRepository;
    private final ScanRecordRepository scanRecordRepository;

    public AdminController(UserRepository userRepository, ScanRecordRepository scanRecordRepository) {
        this.userRepository = userRepository;
        this.scanRecordRepository = scanRecordRepository; //[cite: 44]
    }

    @GetMapping("/telemetry")
    public ResponseEntity<?> getSystemTelemetry() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("total_users", userRepository.count()); //[cite: 44]
        stats.put("total_scans", scanRecordRepository.count()); //[cite: 44]
        return ResponseEntity.ok(stats); //[cite: 44]
    }
}