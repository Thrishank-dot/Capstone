package com.dermosphere.backend.controller;

import com.dermosphere.backend.entity.Role;
import com.dermosphere.backend.entity.User;
import com.dermosphere.backend.repository.RoleRepository;
import com.dermosphere.backend.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Base64;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthController(UserRepository userRepository, RoleRepository roleRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder; //[cite: 46]
    }

    @PostMapping("/login")
    public ResponseEntity<?> authenticateUser(@RequestBody Map<String, String> request) {
        String username = request.get("username");
        String password = request.get("password");
        
        return userRepository.findByUsername(username)
            .filter(user -> passwordEncoder.matches(password, user.getPassword()))
            .map(user -> {
                String token = Base64.getEncoder().encodeToString((username + ":" + password).getBytes());
                return ResponseEntity.ok(Map.of("token", token));
            })
            .orElseGet(() -> ResponseEntity.status(401).body(Map.of("error", "Invalid credentials")));
    }

    @PostMapping("/register")
    public ResponseEntity<?> registerUser(@RequestBody Map<String, String> request) {
        if (userRepository.findByUsername(request.get("username")).isPresent()) {
            return ResponseEntity.badRequest().body("Username explicitly taken."); //[cite: 46]
        }

        User user = new User();
        user.setUsername(request.get("username")); //[cite: 46]
        user.setPassword(passwordEncoder.encode(request.get("password"))); //[cite: 46]
        user.setEmail(request.get("email")); //[cite: 46]
        
        String assignedRole = request.getOrDefault("role", "PATIENT"); //[cite: 46]
        Role role = roleRepository.findByName("ROLE_" + assignedRole.toUpperCase())
                .orElseThrow(() -> new RuntimeException("Role asset target unrecognized in application system mappings.")); //[cite: 46]
        
        user.setRoles(Set.of(role)); //[cite: 46]
        userRepository.save(user); //[cite: 46]

        return ResponseEntity.ok("User registration recorded successfully."); //[cite: 46]
    }
}