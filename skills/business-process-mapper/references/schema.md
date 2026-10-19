# Portable process-map schema

```json
{
  "schemaVersion": "business-process-mapper/1.0",
  "process": {
    "name": "",
    "ownerRole": "",
    "trigger": "",
    "endState": "",
    "outOfScope": [],
    "capability": {"framework": null, "id": null, "label": null, "confidence": "exact|suggested|none"}
  },
  "operatingProfile": {
    "volume": null,
    "frequency": null,
    "standardization": null,
    "impactIfFailure": null,
    "dataSensitivity": [],
    "systems": []
  },
  "nodes": [
    {
      "id": "n1",
      "kind": "trigger|task|decision|wait|end",
      "label": "",
      "description": "",
      "ownerRole": null,
      "inputType": null,
      "output": null,
      "system": null,
      "automationLevel": null,
      "humanReview": false,
      "dataSensitivity": null,
      "improvementOpportunity": null
    }
  ],
  "edges": [{"from": "n1", "to": "n2", "label": null}],
  "governanceFlags": [],
  "referenceKpis": [],
  "assumptions": [],
  "exceptions": []
}
```

Automation levels: 0 manual, 1 tool-assisted, 2 partially automated, 3 automated with a human checkpoint, 4 fully automated in the normal case. Record current state; keep proposed state inside `improvementOpportunity`.
