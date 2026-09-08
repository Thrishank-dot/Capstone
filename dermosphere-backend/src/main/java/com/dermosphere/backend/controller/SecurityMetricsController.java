package com.dermosphere.backend.controller;

import com.dermosphere.backend.entity.User;
import com.dermosphere.backend.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/v1/security")
public class SecurityMetricsController {

    private final UserRepository userRepository;

    public SecurityMetricsController(UserRepository userRepository) { 
        this.userRepository = userRepository; //[cite: 47]
    }

    @PostMapping("/request-metrics-access")
    public ResponseEntity<?> requestAccess(Principal principal) {
        if (principal == null) return ResponseEntity.status(401).build(); 
        
        Optional<User> userOpt = userRepository.findByUsername(principal.getName()); 
        if (userOpt.isPresent()) {
            User user = userOpt.get();
            
            // Bypass pending status for Admin users
            boolean isAdmin = user.getRoles().stream()
                    .anyMatch(r -> r.getName().equalsIgnoreCase("ROLE_ADMIN"));
            
            if (isAdmin) {
                user.setMetricsAccessStatus("GRANTED");
                userRepository.save(user);
                return ResponseEntity.ok(Map.of("status", "GRANTED", "message", "Admin clearance verified."));
            }

            user.setMetricsAccessStatus("PENDING"); 
            userRepository.save(user); 
            return ResponseEntity.ok(Map.of("status", "PENDING", "message", "Request transmitted to Admin Overlord.")); 
        }
        return ResponseEntity.badRequest().build(); 
    }

    @GetMapping("/metrics-status")
    public ResponseEntity<?> checkStatus(Principal principal) {
        if (principal == null) return ResponseEntity.status(401).build(); 
        
        Optional<User> userOpt = userRepository.findByUsername(principal.getName()); 
        if (userOpt.isPresent()) {
            User user = userOpt.get();
            
            // Admin users always receive GRANTED status
            boolean isAdmin = user.getRoles().stream()
                    .anyMatch(r -> r.getName().equalsIgnoreCase("ROLE_ADMIN"));
            
            if (isAdmin) {
                return ResponseEntity.ok(Map.of("status", "GRANTED"));
            }
            
            return ResponseEntity.ok(Map.of("status", user.getMetricsAccessStatus() != null ? user.getMetricsAccessStatus() : "NONE")); 
        }
        return ResponseEntity.badRequest().build(); 
    }
}