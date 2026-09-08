package com.dermosphere.backend.event;

import com.dermosphere.backend.entity.SystemAuditLog;
import com.dermosphere.backend.repository.AuditLogRepository;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

@Component
public class AuditEventListener {

    private final AuditLogRepository auditLogRepository;

    public AuditEventListener(AuditLogRepository auditLogRepository) {
        this.auditLogRepository = auditLogRepository;
    }

    // @Async tells Spring to run this method on the "auditTaskExecutor" thread pool we created earlier
    @Async("auditTaskExecutor")
    @EventListener
    public void handleAuditLogging(AuditEvent event) {
        try {
            SystemAuditLog log = new SystemAuditLog();
            log.setActorUsername(event.getUsername());
            log.setActionCategory(event.getCategory());
            log.setActionDetails(event.getDetails());
            log.setThreatLevel(event.getThreatLevel());
            
            // Save to MySQL
            auditLogRepository.save(log);
            System.out.println("[AUDIT SYSTEM] Logged asynchronous action: [" + event.getCategory() + "] by user " + event.getUsername());
            
        } catch (Exception e) {
            System.err.println("[CRITICAL] Failed to write to audit ledger: " + e.getMessage());
        }
    }
}