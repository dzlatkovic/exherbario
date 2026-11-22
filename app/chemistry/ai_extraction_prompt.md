I am entering published chemical results into Ex Herbario (HERBAR), an archive that links plant chemistry to herbarium voucher specimens. Read the attached paper and its supplementary files, and produce import tables in exactly the format below. Accuracy matters more than completeness: I will check every value before anything is saved.

RULES
1. Copy values exactly as printed. Do not calculate, convert, round, normalise or fill gaps. If a value is unclear, leave the cell empty and say why in the Source column.
2. Keep the paper's compound names as printed. Do not replace them with other names.
3. Trace amounts: write tr. Not detected: write nd. Leave a cell empty only where the paper gives nothing.
4. Leave out summary rows (totals, "monoterpene hydrocarbons", "total identified" and similar).
5. Give every row a Source: the table or figure and the page, e.g. "Table 2, p. 5".
6. Do not invent identifiers. Give a CAS number, PubChem CID or SMILES only where the paper or its supplement prints it. For a compound whose structure is only drawn (for example a new compound), write the SMILES from the drawing, with stereochemistry only as drawn, and write "SMILES from Figure N" in Source.
7. If the paper reports analyses under different conditions (for example two GC columns), make one table for each set of conditions.
8. Use exactly the column headers given below, in that order. Leave out a column the paper does not report. Add no other columns.

TABLE A – chromatographic profiles (GC-MS, GC-FID, LC-MS, HPLC). One row per compound, one column per sample.
No. | Compound | RT | RI exp | RI lit | Identification | Level | CAS | m/z | Adduct | [one column per sample] | Source
- [one column per sample]: headed with the sample code used in the paper; the values as printed (percentages, amounts or areas).
- Identification: the basis the paper gives, using RI, MS, standard, co-injection, MS/MS, literature, separated by semicolons.
- Level: the MSI identification level (1 to 4), only if the paper states it.

TABLE B – isolated compounds. One row per compound.
Compound | SMILES | [sample code] | Purity (%) | NMR experiments | Solvent | New or known | Literature DOI | Optical rotation | ECD | CCDC | Configuration type | Configuration | Identification | Level | m/z | Adduct | Δ ppm | Source
- [sample code]: a column headed with the code of the sample (or extract) the compounds were isolated from; values are the isolated amounts in mg as printed.
- NMR experiments: for example 1H, 13C, DEPT, COSY, HSQC, HMBC, NOESY.
- New or known: new or known. Literature DOI: the DOI of the reference a known compound was compared with, if the paper gives it.
- Configuration type: absolute, relative or not determined. Configuration: how it was determined, as the paper says.
- Identification: NMR, HRMS, X-ray, ECD, standard, co-injection, literature, separated by semicolons.

SECTION C – samples, preparations and runs, as a list of "Field: value" lines. Write "not stated" where the paper gives nothing.
- For each sample: sample code; plant name as printed; voucher specimen number(s) and herbarium; plant part; fresh or dried; collection date; locality; phenological stage.
- For each preparation: essential oil or extract; method and parameters (for example hydrodistillation, Clevenger apparatus, 3 h); plant material mass (g); yield (% w/w).
- For each analysis: technique; column name and dimensions; stationary phase; temperature programme; carrier gas; alkane series used for RI; RI type (temperature-programmed or isothermal). For LC: mobile phase, gradient, ionisation mode, mass analyser. For isolation: isolation procedure, NMR spectrometer and frequency, HRMS instrument and ionisation.

OUTPUT
Give Tables A and B as tables I can paste into Excel (or as CSV), then Section C. Finish with a list of everything you were unsure about, with the table and row.
