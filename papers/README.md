# Paper catalog

Papers are the top-level scientific unit. Each papers/PAPER_ID directory contains:

    paper.yaml
    paper/
    resources/
    capsules/CAPSULE_ID/VERSION/
      capsule.yaml
      public/
      private/

paper.yaml owns the clean list of capsule IDs, versions, statuses, and relative paths. Capsule
manifests identify their paper_id but do not duplicate paper metadata or shared materials.
