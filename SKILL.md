---
name: watermark-id
description: Watermark a copy of an identity document (passport, ID card, residence permit, driving licence, RIB, proof of address, tax notice, payslip) with recipient, purpose and date before it is sent, uploaded or attached anywhere. Use whenever such a scan is about to leave the user's machine, or the user asks to watermark a document.
---

# watermark-id

A watermarked copy names who it was for and why, so a leaked or resold copy is useless for opening accounts elsewhere. This is the practice French public services recommend (filigrane.beta.gouv.fr); the script does the same locally so the document is never uploaded to a watermarking service.

## Steps

1. **Name the recipient and purpose** from the conversation: the organisation receiving the copy and the procedure, e.g. `Example Bank` / `ouverture contrat assurance vie`. Ask the user when either is unclear, since a vague watermark ("copie") protects little.
2. **Check for automated identity verification.** If the upload goes to a KYC flow (selfie plus document capture, or a vendor such as Ubble, Onfido, IDnow, Veriff), a watermark may fail the automated check. Tell the user and let him choose whether to send it unwatermarked. Ordinary uploads, email attachments and portal messages get the watermark.
3. **Run the script** on each file. Use `--lang fr` (default) for French recipients and `--lang en` otherwise:

   ```sh
   <skill-dir>/scripts/watermark.py <file> --recipient "<org>" --purpose "<procedure>" [--lang en]
   ```

   It accepts JPEG, PNG, HEIC, WebP and PDF; writes `<name>-watermarked-<recipient>.<ext>` beside the original and prints the path. PDFs come out flattened (rasterised), and all outputs drop EXIF/GPS metadata. `--text` replaces the template; `--opacity` (0–255, default 95) adjusts strength.
4. **Look at the result**: render a downscaled preview (`magick <out> -resize 1200x1200 <scratch>/preview.jpg`, or `magick -density 60 "<out.pdf>[0]" …` for a PDF) and read it. Done when the watermark covers the whole document and every field, the photo and the MRZ remain legible.
5. **Send the watermarked file** in place of the original wherever it was going, and mention to the user that it is watermarked and for whom.
