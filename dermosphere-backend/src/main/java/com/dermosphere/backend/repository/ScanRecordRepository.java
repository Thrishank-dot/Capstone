
package com.dermosphere.backend.repository;
import com.dermosphere.backend.entity.ScanRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ScanRecordRepository extends JpaRepository<ScanRecord, Long> {
    List<ScanRecord> findByPatientIdOrderByScannedAtDesc(Long patientId);
    // Dynamic triage dashboard querying strategy: Pushes HIGH tier records to the top
    List<ScanRecord> findAllByOrderByTriageTierDescScannedAtDesc();
}