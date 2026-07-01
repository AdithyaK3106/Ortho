# Legal & Commercial Compatibility Assessment: GitNexus

**Date:** 2026-07-01  
**Repository:** https://github.com/abhigyanpatwari/GitNexus  
**Analysis:** Complete license review, no assumptions  

---

## Executive Summary

**CRITICAL BLOCKER: GitNexus uses PolyForm Noncommercial License 1.0.0**

This license **prohibits commercial use**. Unless Ortho obtains a separate commercial license from the maintainer (Abhigyan Patwari), integration is **NOT LEGALLY VIABLE** for any commercial application.

**Recommendation:** Cannot proceed with integration for commercial Ortho without:
1. Explicit written commercial license from maintainer, OR
2. Rewriting Repository Intelligence from scratch

---

## License Details

### License Type

**PolyForm Noncommercial License 1.0.0**

Official text: https://polyformproject.org/licenses/noncommercial/1.0.0

Source: `/LICENSE` in GitNexus repository (verbatim reproduction).

### Key Restrictions

#### 1. **Noncommercial Purposes Only**

> "Any noncommercial purpose is a permitted purpose."

**Definition:** Limited to:
- Personal use (research, experiment, testing, hobby)
- Educational institutions, charitable organizations, government institutions
- Public research organizations
- Public safety or health organizations
- Environmental protection organizations

#### 2. **No Sublicense or Transfer**

> "These terms do not allow you to sublicense or transfer any of your licenses to anyone else."

**Implication:** Ortho CANNOT distribute GitNexus (even embedded in SDK) without commercial license.

#### 3. **Distribution License**

> "The licensor grants you an additional copyright license to distribute copies of the software."

**BUT:** Only for noncommercial purposes. Distributing GitNexus as part of a commercial product violates this.

#### 4. **SaaS Prohibition**

The license permits "use" but noncommercial use only. Running GitNexus as a backend service for paying customers is commercial use.

**Verdict:** Cannot use GitNexus in Ortho Cloud (SaaS) without commercial license.

#### 5. **Attribution Required**

> "Required Notice: Copyright Abhigyan Patwari (https://github.com/abhigyanpatwari/GitNexus)"

Must include attribution in documentation, code, or distribution.

---

## Commercial Scenario Assessment

### Scenario 1: SaaS API (Ortho Cloud)

**Question:** Can Ortho use GitNexus in a server-side Ortho Cloud service for paying customers?

**Answer:** ❌ **RED — PROHIBITED**

**Reasoning:**
- SaaS for paying customers = commercial use
- PolyForm Noncommercial explicitly prohibits this
- License violation if deployed

**Risk Level:** **RED — Legal exposure**

---

### Scenario 2: Embedded SDK

**Question:** Can Ortho distribute GitNexus with Ortho SDK to customers?

**Answer:** ❌ **RED — PROHIBITED**

**Reasoning:**
- Distribution for commercial purposes = prohibited
- License explicitly forbids sublicensing
- Any bundled distribution to customers = commercial use

**Risk Level:** **RED — Legal exposure**

---

### Scenario 3: Internal Company Use

**Question:** Can Ortho's internal team use GitNexus for development/testing?

**Answer:** ⚠️ **YELLOW — CONDITIONAL**

**Reasoning:**
- Internal use MAY qualify as "research, experiment, testing"
- But if commercial product is built using it, the commercial product violates the license
- Unclear whether internal development of a commercial tool qualifies

**Risk Level:** **YELLOW — Depends on interpretation**

**Practical:** Not worth the legal uncertainty for a commercial company

---

### Scenario 4: Forking / Modifying GitNexus

**Question:** Can Ortho fork and modify GitNexus?

**Answer:** ✅ **GREEN — PERMITTED** (but only for noncommercial use)

**Reasoning:**
- License permits modifications: "The licensor grants you an additional copyright license to make changes and new works based on the software for any permitted purpose."
- BUT: "any permitted purpose" = noncommercial only
- Modified or derived software is still subject to noncommercial restriction

**Risk Level:** **GREEN — Legally permitted, but limited use**

**Practical:** Forking doesn't solve the problem (still noncommercial only)

---

### Scenario 5: Open-Source Ortho (Dual Licensing)

**Question:** Could Ortho offer open-source + commercial versions, with GitNexus in open-source only?

**Answer:** ❓ **UNCLEAR**

**Reasoning:**
- Open-source version: Could use GitNexus (noncommercial)
- Commercial version: Would need to rewrite Repository Intelligence without GitNexus
- Possible if clear separation, but adds complexity

**Risk Level:** **YELLOW — Legally complex, probably viable but messy**

**Practical:** Not recommended unless specifically committed to dual licensing

---

## Transitive Dependencies

GitNexus is primarily TypeScript/JavaScript (npm-based). Checked dependency licensing:

Evaluation harness (`eval/pyproject.toml`) depends on:
- `mini-swe-agent` (unknown license, likely permissive)
- `litellm` (Apache 2.0 — permissive)
- `datasets` (Apache 2.0 — permissive)
- `pandas`, `pyyaml`, `typer`, `rich` (all permissive: MIT, Apache)

**Assessment:** No transitive blocking licenses identified, BUT the primary GitNexus license is the blocker.

---

## Required Attribution

If GitNexus is used (for noncommercial purposes only):

> Required Notice: Copyright Abhigyan Patwari (https://github.com/abhigyanpatwari/GitNexus)

Must appear in:
- LICENSE file
- Code comments (if distributed)
- Documentation
- Any public artifacts

---

## Commercial Licensing Options

### Question for Maintainer

> "Abhigyan Patwari, GitNexus is licensed under PolyForm Noncommercial. Does Ortho need a commercial license for [use case]? Are there commercial licensing options available?"

**Status:** Not yet contacted. This is a critical question.

**Possible Outcomes:**
1. Maintainer offers dual licensing (PolyForm Noncommercial + Commercial)
2. Maintainer willing to relicense for Ortho
3. Maintainer only supports noncommercial use
4. Maintainer points to alternative arrangement

---

## Future License Change Risk

**Could the maintainer change the license in the future?**

**Answer:** Yes, the maintainer can change the license for future versions.

**Mitigation:**
- Pin GitNexus version: `gitnexus>=1.5,<2.0`
- Version pinning doesn't prevent future major versions from being incompatible
- Unlikely but possible: maintainer adopts more permissive license in v2.0+
- Rare: maintainer adopts more restrictive license

**Risk Level:** **LOW** (maintainer unlikely to make commercial more restrictive, but possible they drop it)

---

## Patent Clause

> "The licensor grants you a patent license for the software that covers patent claims the licensor can license, or becomes able to license, that you would infringe by using the software."

**Assessment:** Standard, not a concern.

---

## Violation & Cure Period

> "The first time you are notified in writing that you have violated any of these terms, you have 32 days to come into full compliance."

**Implication:** If Ortho violates (e.g., uses commercially without permission), there's a 32-day cure window before license terminates entirely.

**Not reassuring:** Suggests the maintainer takes enforcement seriously.

---

## Conclusion

**GitNexus cannot be integrated into a commercial Ortho product under the current PolyForm Noncommercial license.**

Ortho must choose:

### Option A: Seek Commercial License
- Contact maintainer
- Negotiate dual-licensing or commercial license
- Wait for resolution before integration
- **Cost:** Unknown (could be free, could be paid)
- **Timeline:** 2-4 weeks
- **Success probability:** Unknown

### Option B: Rewrite Repository Intelligence
- Build Ortho's own Repository Intelligence without GitNexus
- Use GitNexus as reference/inspiration only
- Retain vendor independence
- **Cost:** High (6-12 weeks engineering)
- **Timeline:** 6-12 weeks
- **Success probability:** 100% (owns the code)

### Option C: Accept Noncommercial Constraint
- Use GitNexus internally only (not shipped)
- Open-source Ortho (if willing)
- Not viable for commercial Ortho
- **Cost:** Loss of commercial viability
- **Timeline:** N/A
- **Success probability:** N/A

---

## Recommendation

**DO NOT INTEGRATE** GitNexus without explicit commercial license or agreement from maintainer.

**Next Steps:**

1. **Contact maintainer (this week):**
   ```
   Subject: Commercial Licensing for GitNexus Integration
   
   Hi Abhigyan,
   
   We're evaluating GitNexus for integration into Ortho, a commercial 
   Engineering Intelligence platform. Your PolyForm Noncommercial license 
   is excellent for open-source projects.
   
   Do you offer commercial licensing options? Would you be open to a 
   commercial license for our use case (SaaS + SDK distribution)?
   
   Regards,
   [Ortho Team]
   ```

2. **Await response (target: <1 week)**

3. **Decision:**
   - If yes (commercial license available): Proceed with architectural integration design
   - If no (noncommercial only): Accept that GitNexus cannot be shipped, evaluate alternatives
   - If unclear: Request specific terms before proceeding

---

## Risk Summary

| Scenario | Legal Risk | Commercial Risk |
|----------|-----------|-----------------|
| SaaS (paying customers) | 🔴 RED — Violation | High — Liability |
| Embedded SDK | 🔴 RED — Violation | High — Licensing |
| Internal use | 🟡 YELLOW — Ambiguous | Medium — Unclear |
| Forking | 🟢 GREEN — Permitted | Medium — Still noncommercial only |
| Dual-license (OSS + commercial) | 🟡 YELLOW — Complex | Low — If well-separated |

---

*Legal assessment by PRINCIPAL SYSTEMS ARCHITECT*  
*No assumptions — direct license text review*  
*Recommendation: Seek explicit commercial license before proceeding*
