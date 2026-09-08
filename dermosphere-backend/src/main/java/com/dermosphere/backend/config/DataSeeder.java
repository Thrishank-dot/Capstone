package com.dermosphere.backend.config;

import com.dermosphere.backend.entity.Role;
import com.dermosphere.backend.entity.User;
import com.dermosphere.backend.repository.RoleRepository;
import com.dermosphere.backend.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.util.Collections;

@Component
public class DataSeeder implements CommandLineRunner {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;

    public DataSeeder(UserRepository userRepository, RoleRepository roleRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder; //[cite: 41]
    }

    @Override
    public void run(String... args) {
        Role adminRole = createRoleIfNotFound("ROLE_ADMIN");
        Role patientRole = createRoleIfNotFound("ROLE_PATIENT");
        Role doctorRole = createRoleIfNotFound("ROLE_DOCTOR"); //[cite: 41]

        createUserIfNotFound("admin", "admin@dermosphere.com", "admin123", adminRole);
        createUserIfNotFound("patient", "patient@dermosphere.com", "password", patientRole);
        createUserIfNotFound("doctor", "doctor@dermosphere.com", "password", doctorRole); //[cite: 41]
    }

    private Role createRoleIfNotFound(String name) {
        return roleRepository.findByName(name).orElseGet(() -> {
            Role role = new Role();
            role.setName(name);
            return roleRepository.save(role);
        }); //[cite: 41]
    }

    private void createUserIfNotFound(String username, String email, String password, Role role) {
        if (userRepository.findByUsername(username).isEmpty()) {
            User user = new User();
            user.setUsername(username);
            user.setEmail(email);
            user.setPassword(passwordEncoder.encode(password));
            user.setRoles(Collections.singleton(role));
            userRepository.save(user); //[cite: 41]
        }
    }
}