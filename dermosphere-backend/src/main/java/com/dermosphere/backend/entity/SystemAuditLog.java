package com.dermosphere.backend.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "system_audit_logs")
public class SystemAuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "actor_username", nullable = false)
    private String actorUsername;

    @Column(name = "action_category", nullable = false)
    private String actionCategory;

    @Column(name = "action_details", columnDefinition = "TEXT", nullable = false)
    private String actionDetails;

    @Column(name = "threat_level")
    private String threatLevel = "LOW";

    @Column(name = "ip_address")
    private String ipAddress = "127.0.0.1";

    @Column(name = "timestamp", updatable = false)
    private LocalDateTime timestamp;

    @PrePersist
    protected void onCreate() {
        this.timestamp = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getActorUsername() { return actorUsername; }
    public void setActorUsername(String actorUsername) { this.actorUsername = actorUsername; }
    public String getActionCategory() { return actionCategory; }
    public void setActionCategory(String actionCategory) { this.actionCategory = actionCategory; }
    public String getActionDetails() { return actionDetails; }
    public void setActionDetails(String actionDetails) { this.actionDetails = actionDetails; }
    public String getThreatLevel() { return threatLevel; }
    public void setThreatLevel(String threatLevel) { this.threatLevel = threatLevel; }
    public String getIpAddress() { return ipAddress; }
    public void setIpAddress(String ipAddress) { this.ipAddress = ipAddress; }
    public LocalDateTime getTimestamp() { return timestamp; }
}