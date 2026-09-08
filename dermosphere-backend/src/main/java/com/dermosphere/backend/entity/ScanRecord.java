package com.dermosphere.backend.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "scan_records")
public class ScanRecord {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long patientId;

    // --- NEW: YouTube-Style Features ---
    
    @Column(name = "lesion_group_id", length = 100)
    private String lesionGroupId; // THE "PLAYLIST": Groups scans of the exact same mole over time
    
    @Column(name = "is_public", columnDefinition = "boolean default true")
    private Boolean isPublic = true; // THE "FEED": Allows anonymized display on the Global Triage Board
    
    @Column(columnDefinition = "integer default 0")
    private Integer upvotes = 0; // Engagement tracking: Doctors who agreed with AI
    
    @Column(columnDefinition = "integer default 0")
    private Integer downvotes = 0; // Engagement tracking: Doctors who disagreed with AI

    // --- Core File & ML Properties ---

    @Column(nullable = false)
    private String originalFilename;

    @Column(nullable = false, length = 555)
    private String storedFilePath;

    private String predictedClass;
    private Double confidenceScore;
    
    @Column(nullable = false)
    private Integer triageTier = 1; 
    
    private String heatmapPath;
    
    private String doctorFeedback = "PENDING"; 
    
    private LocalDateTime scannedAt = LocalDateTime.now();

    // ==========================================
    // GETTERS AND SETTERS
    // ==========================================

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public Long getPatientId() { return patientId; }
    public void setPatientId(Long patientId) { this.patientId = patientId; }

    public String getLesionGroupId() { return lesionGroupId; }
    public void setLesionGroupId(String lesionGroupId) { this.lesionGroupId = lesionGroupId; }

    public Boolean getIsPublic() { return isPublic; }
    public void setIsPublic(Boolean isPublic) { this.isPublic = isPublic; }

    public Integer getUpvotes() { return upvotes; }
    public void setUpvotes(Integer upvotes) { this.upvotes = upvotes; }

    public Integer getDownvotes() { return downvotes; }
    public void setDownvotes(Integer downvotes) { this.downvotes = downvotes; }

    public String getOriginalFilename() { return originalFilename; }
    public void setOriginalFilename(String originalFilename) { this.originalFilename = originalFilename; }
    
    public String getStoredFilePath() { return storedFilePath; }
    public void setStoredFilePath(String storedFilePath) { this.storedFilePath = storedFilePath; }
    
    public String getPredictedClass() { return predictedClass; }
    public void setPredictedClass(String predictedClass) { this.predictedClass = predictedClass; }
    
    public Double getConfidenceScore() { return confidenceScore; }
    public void setConfidenceScore(Double confidenceScore) { this.confidenceScore = confidenceScore; }
    
    public Integer getTriageTier() { return triageTier; }
    public void setTriageTier(Integer triageTier) { this.triageTier = triageTier; }
    
    public String getHeatmapPath() { return heatmapPath; }
    public void setHeatmapPath(String heatmapPath) { this.heatmapPath = heatmapPath; }
    
    public String getDoctorFeedback() { return doctorFeedback; }
    public void setDoctorFeedback(String doctorFeedback) { this.doctorFeedback = doctorFeedback; }
    
    public LocalDateTime getScannedAt() { return scannedAt; }
    public void setScannedAt(LocalDateTime scannedAt) { this.scannedAt = scannedAt; }
}