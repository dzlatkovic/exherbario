# Preparing a results table with an AI assistant

Back to the [documentation home](index.md).

Ex Herbario has no built-in AI: researchers use the assistant they already have (Claude, ChatGPT or another) to turn a published paper into an import table, and every value then goes through the normal import preview and compound review.

1. On the study page, open **Add data → Prepare the table from a paper with your AI assistant**. Copy the prompt and download the import template (`GET /api/chemistry/import-template.xlsx`).
2. Give the assistant the prompt together with the paper's PDF and supplementary files.
3. Paste Table A (chromatographic profiles) into the template's *GC-MS profile* sheet, or Table B (isolated compounds) into *Isolated compounds*. Rename the sample columns to your sample codes. Section C is for you: use it when creating samples and preparations and in the run settings.
4. Upload the file with **Import a results table** and check every value against the paper. The import recognises the template's headers, ignores the `Source` column, and flags percentages above 100%, RIs far from their reference, invalid SMILES and m/z values that do not match the formula.

The prompt is kept in [`app/chemistry/ai_extraction_prompt.md`](https://github.com/dzlatkovic/exherbario/blob/main/app/chemistry/ai_extraction_prompt.md); the study page shows the same text. It asks the assistant to copy values exactly, to mark trace and not-detected values, to leave out summary rows, to give each row its source, and to give identifiers and SMILES only where the paper prints or draws them.

AI extraction is a data-entry aid. The author remains responsible for the values, and should treat SMILES written from drawings and any value the assistant marked as uncertain with particular care.
