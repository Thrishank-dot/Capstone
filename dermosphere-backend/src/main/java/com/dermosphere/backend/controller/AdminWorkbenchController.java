package com.dermosphere.backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/admin/workbench")
public class AdminWorkbenchController {

    @PostMapping("/execute-sql")
    public ResponseEntity<?> executeSql(@RequestBody Map<String, String> payload) {
        String query = payload.get("query");
        if (query != null && query.toLowerCase().contains("drop")) {
            return ResponseEntity.status(403).body(Map.of("error", "DROP statements strictly prohibited."));
        }

        List<Map<String, Object>> mockData = List.of(
                Map.of("id", 1, "username", "johndoe", "email", "john@example.com", "ip", "192.168.1.1"),
                Map.of("id", 2, "username", "mariasmith", "email", "maria@test.com", "ip", "10.0.0.4")
        );

        return ResponseEntity.ok(Map.of("data", mockData));
    }
}