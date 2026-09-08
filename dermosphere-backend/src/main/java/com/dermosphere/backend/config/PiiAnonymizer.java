package com.dermosphere.backend.config;

import org.springframework.stereotype.Component;
import java.security.MessageDigest;
import java.util.Base64;

@Component
public class PiiAnonymizer {
    
    public String maskPatientIdentity(Long patientId) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(String.valueOf(patientId).getBytes());
            return Base64.getEncoder().encodeToString(hash).substring(0, 12); //[cite: 42]
        } catch (Exception e) {
            return "ANON-0000"; //[cite: 42]
        }
    }
}