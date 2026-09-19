param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-JsonFile([string]$Path) {
    $utf8 = [System.Text.UTF8Encoding]::new($false, $true)
    return [System.IO.File]::ReadAllText($Path, $utf8) | ConvertFrom-Json
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Hash-Text([string]$Content) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Content)
    $hash = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
    } finally {
        $hash.Dispose()
    }
}

function Markdown-Cell([object]$Value) {
    if ($null -eq $Value) { return "" }
    return ([string]$Value).Replace("|", "\\|").Replace("`r", " ").Replace("`n", " ")
}

$rolePath = Join-Path $RepositoryRoot "config/topic_structural_role_authority/structural-role-authority-20260912.v4.json"
$topicPath = Join-Path $RepositoryRoot "config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json"
$outDir = Join-Path $RepositoryRoot "docs/reports/TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002/d001-owner-review-draft"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$roleArtifact = Read-JsonFile $rolePath
$topicArtifact = Read-JsonFile $topicPath
$roleFileHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $rolePath).Hash.ToLowerInvariant()
$topicFileHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $topicPath).Hash.ToLowerInvariant()

$topicById = @{}
foreach ($topic in @($topicArtifact.topics)) {
    $topicById[[string]$topic.topicId] = $topic
}

$parentByLeaf = @{}
foreach ($link in @($topicArtifact.hierarchy)) {
    $parentByLeaf[[string]$link.childTopicId] = [string]$link.parentTopicId
}

$leafTopics = @(
    @($topicArtifact.topics) |
        Where-Object { $_.level -eq "LEAF" -and $_.status -eq "ENABLED" } |
        Sort-Object @{Expression = { [string]$_.name }}, @{Expression = { [string]$_.topicId }}
)
if ($leafTopics.Count -ne [int]$topicArtifact.expectedLeafCount) {
    throw "Leaf topic count mismatch: expected $($topicArtifact.expectedLeafCount), actual $($leafTopics.Count)"
}

$coreByTopic = @{}
foreach ($row in @($roleArtifact.rows | Where-Object { $_.structuralRole -eq "CORE" })) {
    $topicId = [string]$row.topicId
    if (-not $coreByTopic.ContainsKey($topicId)) { $coreByTopic[$topicId] = @() }
    $coreByTopic[$topicId] = @($coreByTopic[$topicId]) + @($row)
}
foreach ($topicId in @($coreByTopic.Keys)) {
    $coreByTopic[$topicId] = @(
        $coreByTopic[$topicId] |
            Sort-Object @{Expression = { "{0}:{1}" -f $_.marketCode, $_.instrumentCode }}, @{Expression = { [string]$_.relationId }}
    )
}

$topicRecords = @()
$candidateRows = @()
$reviewOrder = 0
foreach ($topic in $leafTopics) {
    $topicId = [string]$topic.topicId
    $parentId = if ($parentByLeaf.ContainsKey($topicId)) { $parentByLeaf[$topicId] } else { $null }
    $parent = if ($parentId -and $topicById.ContainsKey($parentId)) { $topicById[$parentId] } else { $null }
    $coreCandidates = @()
    if ($coreByTopic.ContainsKey($topicId)) {
        $coreCandidates = @($coreByTopic[$topicId])
    }
    $candidateState = if ($coreCandidates.Count -eq 0) { "NO_FORMAL_CORE_CANDIDATES" } elseif ($coreCandidates.Count -eq 1) { "ONE_CORE_CANDIDATE" } else { "MULTIPLE_CORE_CANDIDATES" }
    $topicReviewState = if ($coreCandidates.Count -eq 0) { "PENDING_OWNER_REVIEW_NO_CORE_CANDIDATE" } else { "PENDING_OWNER_REVIEW" }
    $topicCandidates = @()

    foreach ($candidate in $coreCandidates) {
        $reviewOrder++
        $record = [ordered]@{
            reviewOrder = $reviewOrder
            topicId = $topicId
            topicName = [string]$topic.name
            parentTopicId = $parentId
            parentTopicName = if ($parent) { [string]$parent.name } else { $null }
            marketCode = [string]$candidate.marketCode
            instrumentCode = [string]$candidate.instrumentCode
            canonicalReviewIdentifier = "{0}:{1}" -f $candidate.marketCode, $candidate.instrumentCode
            relationId = [string]$candidate.relationId
            relationVersion = [string]$candidate.relationVersion
            structuralRole = "CORE"
            approvalState = [string]$candidate.approvalState
            authorityVersion = [string]$roleArtifact.authorityVersion
            authorityEffectiveFrom = [string]$roleArtifact.effectiveDate
            sourceReference = [string]$candidate.sourceReference
            sourceArtifactId = "structural-role-authority:$($roleArtifact.authorityVersion)"
            sourceArtifactHash = [string]$roleArtifact.artifactSha256
            inclusionState = "PENDING_OWNER_REVIEW"
            proposedInclude = "PENDING_OWNER_REVIEW"
            proposedImportance = "PENDING_OWNER_REVIEW"
            historicalEvidenceState = "NONE_RECOVERED"
            ownerReviewState = "PENDING_OWNER_REVIEW"
            formalRuntimeAuthority = "NOT_FORMAL_UNTIL_OWNER_APPROVAL"
            reviewFlags = @("FORMAL_CORE_CANDIDATE_ONLY", "NO_D001_INCLUDE_OR_IMPORTANCE_INFERENCE")
        }
        $candidateRows += ,$record
        $topicCandidates += ,$record
    }

    $topicRecords += ,[ordered]@{
        topicId = $topicId
        topicName = [string]$topic.name
        topicSlug = [string]$topic.slug
        parentTopicId = $parentId
        parentTopicName = if ($parent) { [string]$parent.name } else { $null }
        level = [string]$topic.level
        status = [string]$topic.status
        authorityEffectiveFrom = [string]$roleArtifact.effectiveDate
        coreCandidateCount = $coreCandidates.Count
        candidateState = $candidateState
        projectionReviewState = $topicReviewState
        formalRuntimeAuthority = "NOT_FORMAL_UNTIL_OWNER_APPROVAL"
        reviewFlags = if ($coreCandidates.Count -eq 0) { @("NO_FORMAL_CORE_CANDIDATES", "FAIL_CLOSED_IF_UNAPPROVED") } else { @("OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS") }
        candidates = @($topicCandidates)
    }
}

$noCoreTopics = @($topicRecords | Where-Object { $_.coreCandidateCount -eq 0 })
$oneCoreTopics = @($topicRecords | Where-Object { $_.coreCandidateCount -eq 1 })
$multiCoreTopics = @($topicRecords | Where-Object { $_.coreCandidateCount -gt 1 })
$summary = [ordered]@{
    leafTopics = $leafTopics.Count
    coreCandidateRows = $candidateRows.Count
    csvRowsIncludingNoCandidateTopicPlaceholders = $candidateRows.Count + $noCoreTopics.Count
    topicsFullyRecoveredFromExistingHumanAuthority = 0
    topicsRequiringOwnerReview = $topicRecords.Count
    topicsWithNoFormalCoreCandidates = $noCoreTopics.Count
    topicsWithExactlyOneCoreCandidate = $oneCoreTopics.Count
    topicsWithMultipleCoreCandidates = $multiCoreTopics.Count
    structuralRoleCoreRows = @($roleArtifact.rows | Where-Object { $_.structuralRole -eq "CORE" }).Count
}

$draftBody = [ordered]@{
    schemaVersion = "topic-score-projection-owner-review-draft.v1"
    status = "DRAFT_NOT_FORMAL_AUTHORITY"
    taskId = "TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002"
    decision = "DEC-04=A"
    projectionPolicy = "D001_BOUNDED_OWNER_APPROVED_CORE_SUBSET"
    projectionVersion = "d001-topic-core-score-projection-owner-review-draft.v1"
    sourceStructuralRoleAuthorityVersion = [string]$roleArtifact.authorityVersion
    sourceStructuralRoleAuthorityArtifactHash = [string]$roleArtifact.artifactSha256
    sourceStructuralRoleAuthorityFileSha256 = $roleFileHash
    topicAuthorityArtifact = "config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json"
    topicAuthorityArtifactFileSha256 = $topicFileHash
    effectiveFrom = [string]$roleArtifact.effectiveDate
    asOfSemantics = "PROSPECTIVE_EFFECTIVE_DATE_NO_D1_LOOKAHEAD"
    sourceCandidateBoundary = "APPROVED_EFFECTIVE_STRUCTURAL_ROLE_CORE_ONLY"
    membershipPolicy = "EXPLICIT_OWNER_APPROVED_INCLUDE_OR_EXCLUDE"
    semanticReconciliation = [ordered]@{
        structuralRoleValues = @("REPRESENTATIVE", "CORE", "RELATED")
        historicalRoleWeightEvidence = "NO_FORMAL_LEAD_CORE_RELATE_ROLE_WEIGHT_MAPPING_RECOVERED"
        leadWeight = "UNPROVEN"
        coreWeight = "UNPROVEN"
        relateWeight = "UNPROVEN"
        importanceIsRoleProjection = "NO"
        d001ScoreMemberUniverse = "APPROVED_EFFECTIVE_NON_SUPERSEDED_STRUCTURAL_ROLE_CORE_ROWS"
        d001RequiresSeparateCoreSubset = "YES"
        d001RequiresPerCoreImportance = "YES_FOR_SELECTED_PROJECTION_MEMBERS"
        orderAffectsScore = "NO"
        fixedMinRequiredByFormula = "NO"
        fixedMaxRequiredByFormula = "NO"
        modelClassification = "MODEL_B"
        adjacentLifecycleRolePath = "SHADOW_ONLY_NOT_D001_SCORE_AUTHORITY"
    }
    importancePolicy = [ordered]@{
        allowed = @("1.00", "0.75", "0.50")
        derivation = "PENDING_OWNER_REVIEW"
        semanticSource = "SEPARATE_SCORE_CONSUMER_METADATA_NOT_STRUCTURAL_ROLE_PROJECTION"
        marketDataInference = "PROHIBITED"
    }
    subsetBounds = [ordered]@{
        minimum = "NO_ADDITIONAL_OWNER_IMPOSED_LIMIT"
        maximum = "NO_ADDITIONAL_OWNER_IMPOSED_LIMIT"
        emptyProjection = "FAIL_CLOSED"
    }
    ordering = [ordered]@{
        productPolicyMeaning = "NONE_UNLESS_RECOVERED_SCORE_FORMULA_PROVES_ORDER_DEPENDENCY"
        technicalTieBreak = "CANONICAL_REVIEW_IDENTIFIER_ASCENDING"
        semanticEffect = "NONE"
    }
    ownerReviewGate = "REQUIRED_BEFORE_FORMAL_RUNTIME_ACTIVATION"
    recoveredProposalPolicy = "NONE_RECOVERED; STRUCTURAL_ROLE_CORE_IS_NOT_D001_INCLUDE"
    summary = $summary
    topics = @($topicRecords)
    provenance = [ordered]@{
        structuralRoleSource = "config/topic_structural_role_authority/structural-role-authority-20260912.v4.json"
        topicScopeSource = "config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json"
        generatedBy = "scripts/generate_d001_owner_review_draft.ps1"
        generatedAt = "2026-09-20"
        forbiddenInputs = @("daily return", "price", "volume", "turnover", "market cap", "momentum", "Score", "Grade", "Lifecycle", "Opportunity", "runtime AI")
    }
}

$canonicalBody = $draftBody | ConvertTo-Json -Depth 14 -Compress
$draftArtifactHash = Hash-Text $canonicalBody
$draftBody.draftArtifactSha256 = $draftArtifactHash
$jsonText = $draftBody | ConvertTo-Json -Depth 14
Write-Utf8NoBom (Join-Path $outDir "d001-owner-review-draft.json") $jsonText

$csvRows = @()
foreach ($row in $candidateRows) {
    $csvRows += [pscustomobject]@{
        review_order = $row.reviewOrder
        topic_id = $row.topicId
        topic_name = $row.topicName
        parent_topic_id = $row.parentTopicId
        parent_topic_name = $row.parentTopicName
        market_code = $row.marketCode
        instrument_code = $row.instrumentCode
        canonical_review_identifier = $row.canonicalReviewIdentifier
        relation_id = $row.relationId
        relation_version = $row.relationVersion
        structural_role = $row.structuralRole
        approval_state = $row.approvalState
        authority_version = $row.authorityVersion
        authority_effective_from = $row.authorityEffectiveFrom
        source_reference = $row.sourceReference
        source_artifact_id = $row.sourceArtifactId
        source_artifact_hash = $row.sourceArtifactHash
        inclusion_state = $row.inclusionState
        proposed_include = $row.proposedInclude
        proposed_importance = $row.proposedImportance
        historical_evidence_state = $row.historicalEvidenceState
        owner_review_state = $row.ownerReviewState
        formal_runtime_authority = $row.formalRuntimeAuthority
        review_flags = ($row.reviewFlags -join ";")
    }
}
foreach ($topic in $noCoreTopics) {
    $csvRows += [pscustomobject]@{
        review_order = $null
        topic_id = $topic.topicId
        topic_name = $topic.topicName
        parent_topic_id = $topic.parentTopicId
        parent_topic_name = $topic.parentTopicName
        market_code = $null
        instrument_code = $null
        canonical_review_identifier = $null
        relation_id = $null
        relation_version = $null
        structural_role = "NO_FORMAL_CORE_CANDIDATE"
        approval_state = $null
        authority_version = [string]$roleArtifact.authorityVersion
        authority_effective_from = $topic.authorityEffectiveFrom
        source_reference = "STRUCTURAL_ROLE_ARTIFACT_ENUMERATION"
        source_artifact_id = "structural-role-authority:$($roleArtifact.authorityVersion)"
        source_artifact_hash = [string]$roleArtifact.artifactSha256
        inclusion_state = "PENDING_OWNER_REVIEW"
        proposed_include = "PENDING_OWNER_REVIEW"
        proposed_importance = "PENDING_OWNER_REVIEW"
        historical_evidence_state = "NONE_RECOVERED"
        owner_review_state = "PENDING_OWNER_REVIEW"
        formal_runtime_authority = "FAIL_CLOSED_NO_CORE_CANDIDATE"
        review_flags = "NO_FORMAL_CORE_CANDIDATES;FAIL_CLOSED_IF_UNAPPROVED"
    }
}
$csvText = $csvRows | ConvertTo-Csv -NoTypeInformation | Out-String
$csvPath = Join-Path $outDir "d001-owner-review-draft.csv"
Write-Utf8NoBom $csvPath ($csvText.TrimEnd() + "`n")

$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine("# D001 Owner Review Draft")
[void]$md.AppendLine("")
[void]$md.AppendLine("``STATUS=DRAFT_NOT_FORMAL_AUTHORITY``")
[void]$md.AppendLine("")
[void]$md.AppendLine("This draft was generated under DEC-04=A from the formally approved Structural Role CORE authority. It enumerates candidates only. It does not assign final INCLUDE/EXCLUDE or importance, and it must not be consumed by Score runtime.")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Review contract")
[void]$md.AppendLine("")
[void]$md.AppendLine("- Candidate source: approved Structural Role ``CORE`` rows only.")
[void]$md.AppendLine("- Final membership: Owner-approved ``INCLUDED`` or ``EXCLUDED`` per Leaf Topic.")
[void]$md.AppendLine("- Importance: current D001 contract permits Owner-approved ``1.00``, ``0.75``, or ``0.50``; these are separate Score-consumer metadata, not automatic Structural Role weights.")
[void]$md.AppendLine("- Structural Role mapping: repository evidence does not prove ``LEAD -> 1.00``, ``CORE -> 0.75``, or ``RELATE -> 0.25``; no such mapping is applied.")
[void]$md.AppendLine("- Projection bounds: no additional Owner-imposed minimum or maximum; an absent approved projection remains fail closed.")
[void]$md.AppendLine("- Empty approved projection: fail closed; never substitute all CORE or Leader Set.")
[void]$md.AppendLine("- Ordering: no product-policy meaning; canonical review identifier ascending is used only for deterministic persistence/readback.")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Summary")
[void]$md.AppendLine("")
[void]$md.AppendLine("| Metric | Count |")
[void]$md.AppendLine("|---|---:|")
foreach ($property in $summary.GetEnumerator()) {
    [void]$md.AppendLine("| $(Markdown-Cell $property.Key) | $(Markdown-Cell $property.Value) |")
}
[void]$md.AppendLine("")
[void]$md.AppendLine("``D001_REVIEW_TOPICS=$($summary.leafTopics)``  ")
[void]$md.AppendLine("``D001_REVIEW_CANDIDATES=$($summary.coreCandidateRows)``  ")
[void]$md.AppendLine("``D001_TOPICS_FULLY_RECOVERED_FROM_EXISTING_HUMAN_AUTHORITY=$($summary.topicsFullyRecoveredFromExistingHumanAuthority)``  ")
[void]$md.AppendLine("``D001_TOPICS_REQUIRING_OWNER_REVIEW=$($summary.topicsRequiringOwnerReview)``  ")
[void]$md.AppendLine("``D001_TOPICS_WITH_NO_CORE_CANDIDATES=$($summary.topicsWithNoFormalCoreCandidates)``")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Topics grouped by formal parent")
[void]$md.AppendLine("")
[void]$md.AppendLine("| Parent | Leaf Topic | CORE candidates | Review state | Flags |")
[void]$md.AppendLine("|---|---|---:|---|---|")
foreach ($topic in $topicRecords) {
    [void]$md.AppendLine("| $(Markdown-Cell $topic.parentTopicName) | $(Markdown-Cell $topic.topicName) | $($topic.coreCandidateCount) | $(Markdown-Cell $topic.projectionReviewState) | $(Markdown-Cell ($topic.reviewFlags -join '; ')) |")
}
[void]$md.AppendLine("")
[void]$md.AppendLine("## Topics with no formal CORE candidates")
[void]$md.AppendLine("")
if ($noCoreTopics.Count -eq 0) {
    [void]$md.AppendLine("None.")
} else {
    foreach ($topic in $noCoreTopics) {
        [void]$md.AppendLine("- ``$(Markdown-Cell $topic.topicId)`` $(Markdown-Cell $topic.topicName) - no approved Structural Role CORE candidate; any formal projection must fail closed until authority changes.")
    }
}
[void]$md.AppendLine("")
[void]$md.AppendLine("## Editing and approval handoff")
[void]$md.AppendLine("")
[void]$md.AppendLine("Review the machine-readable JSON/CSV rows. For each candidate, Owner review must set final inclusion and, only for included members, one legal importance value. The reviewed result must receive its own version, effective date, approval reference, source artifact binding, correction/supersession identity, and lineage hash before it can be ingested into ``TopicScoreProjection``.")
[void]$md.AppendLine("")
[void]$md.AppendLine("The generated draft is not a formal runtime authority artifact. No Score, Grade, Lifecycle, Topic, Today, Opportunity, Production, or scheduler state was changed by this generation.")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Provenance")
[void]$md.AppendLine("")
[void]$md.AppendLine("- Structural Role source: ``config/topic_structural_role_authority/structural-role-authority-20260912.v4.json``")
[void]$md.AppendLine("- Structural Role declared artifact hash: ``$($roleArtifact.artifactSha256)``")
[void]$md.AppendLine("- Structural Role file SHA-256: ``$roleFileHash``")
[void]$md.AppendLine("- Topic scope source: ``config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json``")
[void]$md.AppendLine("- Topic scope file SHA-256: ``$topicFileHash``")
[void]$md.AppendLine("- Draft content hash (before embedded hash field): ``$draftArtifactHash``")
[void]$md.AppendLine("- Generator: ``scripts/generate_d001_owner_review_draft.ps1``")
Write-Utf8NoBom (Join-Path $outDir "d001-owner-review-draft.md") $md.ToString()

Write-Output ($draftBody | ConvertTo-Json -Depth 4 -Compress)
