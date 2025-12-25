
# Immich Issue Report: Orphan Albums Cannot Be Managed or Deleted via API

**Repository:** https://github.com/immich-app/immich
**Issue Tracker:** https://github.com/immich-app/immich/issues

---

## Issue Title

Orphan albums (albums without any user) cannot be listed, managed, or deleted via API

---

## Issue Body

### Summary

When an album is created without associating any user, it becomes invisible to all users (including admins) in both the Immich UI and API. These orphan albums cannot be listed, managed, or deleted via the public API, even if their names are known. This leads to the accumulation of inaccessible "ghost" albums that cannot be cleaned up programmatically.

### Steps to Reproduce
1. Create an album via the API without associating any user (by mistake or bug).
2. Try to list all albums using `/albums` or any available endpoint.
3. Notice that the orphan album does not appear in the results.
4. Try to delete the album by name or id (it's not possible to get the id if you can't list it).

### Expected Behavior
- There should be a way to list all albums in the system (at least in admin mode) or filter those without associated users.
- It should be possible to delete orphan albums via the API or admin interface.

### Actual Behavior
- Albums without users become invisible and inaccessible from the API and UI.
- They cannot be listed, searched, or deleted.
- They are only accessible via direct database access.

### Impact
- Accumulation of "ghost" albums that cannot be managed or cleaned up.
- Risk of inconsistencies and unnecessary resource consumption.
- Makes it difficult to correct logic errors in external integrations.

### Technical Context
- The problem was detected while automating album creation from external integrations.
- The Immich OpenAPI wrapper only allows listing albums associated with the authenticated user.
- There is no admin endpoint to list all albums or search by name globally.
- Example orphan album names generated: `2025-12-19 VID-20251219-WA0000.mp4`, `2025-12-18 VID-20251218-WA0002.mp4`, etc.

### Proposal
- Add an admin endpoint to list all albums, with an option to filter those without associated users.
- Allow deleting albums by id even if they are not associated with any user (at least in admin mode).
- Alternatively, prevent the creation of albums without users at the backend level.

### Useful Links
- [Immich Repository](https://github.com/immich-app/immich)
- [Issue Tracker](https://github.com/immich-app/immich/issues)

### Additional Information
- Detected in a mass asset classification and automation environment.
- We have logs with the names of the orphan albums, but cannot access them via API.

---

## Issue Reporting Checklist
- [x] Clear and descriptive title
- [x] Problem summary
- [x] Steps to reproduce
- [x] Expected and actual behavior
- [x] Impact and technical context
- [x] Solution proposal
- [x] Useful links
- [x] Additional information

---

**Ready to copy and paste into the Immich issue tracker.**
