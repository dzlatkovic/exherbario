# Phytochemistry

Results are organised as **study → sample → preparation → run**. A sample is the plant material, linked to one or more vouchers; a preparation is an essential oil, extract or isolate made from it; a run holds the measurements.

## Samples and preparations

On the study page, **Add data → Add sample** links the sample to its vouchers (for example *sampled from voucher* or *same population*) and records the plant part and collection details. **Add preparation** records the method: hydrodistillation, maceration, an isolation procedure. Save methods and run conditions you use often; they appear as choices next time.

A sample and its preparation can be deposited without any run, for example an extract tested only in a bioassay.

## Import a results table

**Import a results table** takes the table from the paper as Excel or CSV: compounds in rows, one column per sample.

1. Upload the file and choose the header row.
2. Assign each column a role (compound, RI, identification, a sample…). The page guesses most of them.
3. Columns not yet linked to a sample: **Create samples and preparations** creates them all in one dialog.
4. Enter the run conditions once (for GC: column, temperature programme, alkane series) and check the preview.
5. **Look up remaining names in PubChem**. Exact name matches are accepted automatically; review the rest, choose another compound, or give a SMILES for a compound PubChem does not have.
6. **Confirm import**. Each sample column becomes one run.

Two kinds of tables are supported:

- **Chromatographic profiles** (GC-MS, GC-FID, LC-MS, HPLC-DAD): amounts per sample, with optional RT, RI (experimental and literature), identification basis and MSI level, m/z and adduct.
- **Isolated compounds**: isolated amount, SMILES for new compounds, NMR experiments and solvent, optical rotation, HRMS, X-ray (CCDC) and configuration. Raw spectra are not needed; the conditions are recorded with the run.

Identification can be written as the paper writes it: `RI; MS; co-injection`, or abbreviations such as `CoI`, `KI`, `Std`, `Lit`.

To start from a published paper, see [Prepare a results table](ai-extraction.md).

## Compounds

Compounds are stored locally by PubChem CID, so saved data and public pages do not depend on PubChem. Structures that PubChem lacks are kept from the authors' SMILES. A wrong compound can be corrected later with a reason; the measurement values are never edited.

## Export

A published study offers **Long CSV** (one row per measurement) and **Wide CSV** (one row per run, one column per compound), ready for statistics in R or Python. In the wide format trace values are `tr` and not-detected values `nd`.
