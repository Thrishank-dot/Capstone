package com.dermosphere.backend.event;

public class AuditEvent {
    private final String username;
    private final String category;
    private final String details;
    private final String threatLevel;

    public AuditEvent(String username, String category, String details, String threatLevel) {
        this.username = username;
        this.category = category;
        this.details = details;
        this.threatLevel = threatLevel;
    }

    public String getUsername() { return username; }
    public String getCategory() { return category; }
    public String getDetails() { return details; }
    public String getThreatLevel() { return threatLevel; }
}