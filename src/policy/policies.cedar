// Kabadi Khata policies. Default deny: anything not permitted below is denied,
// and `forbid` always beats `permit`.

// 1. Kabadiwala: own Chain and Receipts only. No receipt PII, no radar, no flags.
@id("kabadiwala-own-data")
permit (
  principal is Actor in Role::"kabadiwala",
  action in [Action::"create_collection", Action::"read_receipt", Action::"verify_chain"],
  resource
) when { resource has collector && resource.collector == principal };

// 2. Brand: provenance of its own Certificates only (aggregate view, never a Kabadiwala identity).
@id("brand-own-certificates")
permit (
  principal is Actor in Role::"brand",
  action == Action::"read_provenance",
  resource is Certificate
) when { resource has buyer && resource.buyer == principal };

// 3. Auditor: read, verify, run the radar, approve flags.
@id("auditor-oversight")
permit (
  principal is Actor in Role::"auditor",
  action in [Action::"read_receipt", Action::"read_receipt_pii", Action::"verify_chain",
             Action::"run_radar", Action::"read_flags", Action::"approve_flag",
             Action::"read_provenance", Action::"list_actors"],
  resource
);

// 3b. Kabadiwala: may read a Photo by its sha256 (the unguessable hash is the capability) and
// list the directory for the bot. Brands get neither.
@id("kabadiwala-photo")
permit (
  principal is Actor in Role::"kabadiwala",
  action == Action::"read_receipt_pii",
  resource is Photo
);
@id("kabadiwala-list-directory")
permit (
  principal is Actor in Role::"kabadiwala",
  action == Action::"list_actors",
  resource is Directory
);

// 3c. Any known Actor may register only itself; the API refuses to change a non-Kabadiwala.
@id("self-registration")
permit (
  principal is Actor,
  action == Action::"register",
  resource is Actor
) when { resource == principal };

// 4. Agent: its one write, and only after the consistency check passed.
@id("agent-create-receipt")
permit (
  principal == Agent::"kabadi-agent",
  action == Action::"create_receipt",
  resource is Receipt
) when { context.consistency_ok == true };

// 5. Agent: explicitly forbidden from everything else, even if code or policy changes elsewhere.
@id("agent-forbidden")
forbid (
  principal == Agent::"kabadi-agent",
  action in [Action::"approve_flag", Action::"issue_certificate", Action::"read_receipt_pii",
             Action::"read_receipt", Action::"read_provenance", Action::"run_radar",
             Action::"verify_chain", Action::"create_collection", Action::"read_flags",
             Action::"list_actors", Action::"register"],
  resource
);
