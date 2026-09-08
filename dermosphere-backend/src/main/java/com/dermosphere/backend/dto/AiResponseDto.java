package com.dermosphere.backend.dto;

import java.util.Map;

public class AiResponseDto {
    private String status;
    private String prediction;
    private Double confidence;
    private Integer triage_tier;
    private String heatmap_path;
    private Map<String, Double> metrics;

    // Getters and Setters
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getPrediction() { return prediction; }
    public void setPrediction(String prediction) { this.prediction = prediction; }
    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }
    public Integer getTriage_tier() { return triage_tier; }
    public void setTriage_tier(Integer triage_tier) { this.triage_tier = triage_tier; }
    public String getHeatmap_path() { return heatmap_path; }
    public void setHeatmap_path(String heatmap_path) { this.heatmap_path = heatmap_path; }
    public Map<String, Double> getMetrics() { return metrics; }
    public void setMetrics(Map<String, Double> metrics) { this.metrics = metrics; }
}