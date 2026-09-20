"""DNAMAN 4.0 menu command ids and dialog control ids."""

CMD = {
    # File / Edit
    "new": 57600, "open": 57601, "close": 57602, "save": 57603, "save_as": 57604,
    "print": 57607, "exit": 57665,
    "undo": 57643, "redo": 57644, "select_all": 57642, "cut": 57635, "copy": 57634,
    "paste": 57637, "delete": 57632, "find": 57636, "find_next": 57640, "replace": 57641,
    "sequence_format": 210, "enter_sequence": 215,
    # Sequence
    "channel_default": 241, "channel_analysis_def": 240,
    "load_from_selection": 220, "load_from_file": 221, "load_genbank": 222,
    "load_gcg": 223, "load_database": 224, "load_multiple": 228,
    "composition": 251, "reverse": 252, "complement": 253, "revcomp": 254,
    "double_strand": 255, "rna": 256, "protein_seq": 257,
    "blastn": 275, "blastx": 276, "tblastx": 277, "blastp": 278, "tblastn": 279,
    "assembly": 290,
    "search_sequences": 295, "direct_repeats": 296, "mirror_repeats": 297,
    "hairpin": 298, "aa_search": 299, "orf": 300,
    "dot_matrix": 310, "align_two": 315, "align_multiple": 320,
    "random_new": 248, "randomize": 249,
    # Restriction
    "restriction": 325, "cloning": 335, "map_reconstruction": 340, "draw_map": 345,
    "silent_mutation": 347, "directed_mismatch": 348,
    # Primer
    "oligo_manager": 400, "oligo_edit": 401, "oligo_import": 402, "oligo_export": 403,
    "primer_from_input": 410, "primer_from_db": 411,
    "primer_tm": 420, "primer_self": 425, "primer_dna": 426,
    "primer_second_input": 427, "primer_second_db": 428,
    "pcr_primers": 430, "mispriming": 414,
    # Protein
    "genetic_code": 350, "translation_overview": 352, "translation": 355,
    "rev_translation_input": 380, "rev_translation_file": 381,
    "codon_usage_f1": 360, "codon_usage_f2": 361, "codon_usage_f3": 362,
    "aa_composition": 365, "charge_ph": 368,
    "hydrophobicity": 366, "hydrophobicity_all": 383,
    "hydrophilicity": 367, "hydrophilicity_all": 384,
    "secondary_structure": 385,
    # Database / Info
    "db_manager": 440, "db_edit": 455, "db_scan": 460, "db_search_nt": 461, "db_search_aa": 462,
    "info_enzymes": 470, "info_methylase": 480, "info_genetic_code": 482,
    "info_amino_acids": 484, "info_nucleotides": 486, "info_settings": 490,
    # View / Window
    "view_statusbar": 59393,
    "window_cascade": 57650, "window_tile_h": 57651, "window_tile_v": 57652,
}

DLG = {
    "file_name_edit": 1152,
    "ok": 1,
    "cancel": 2,
    "wizard_next": 12324,
    "wizard_back": 12323,
    "wizard_finish": 12325,
    "select_all": 2605,
    "genbank_list": 1063,
    "primer_edit": 1049,
    "aa_search_edit": 1054,
    "mirror_edit": 1049,
    "random_size_edit": 1000,
    "enter_seq_edit": 1048,
    "mismatch_pos_edit": 1265,
    "restriction_circular": 1098,
    "restriction_summary": 1099,
    "restriction_map": 1100,
    "restriction_positions": 1101,
    "restriction_pattern": 1102,
}

FILE_DIALOG_CLASS = "#32770"
DIALOG_CLASS = "#32770"
RICHEDIT_CLASS = "RICHEDIT"
STATUS_CLASS = "msctls_statusbar32"
MDI_CLIENT = "MDIClient"

GENBANK_DIALOG_TITLE = "GenBank"
SEQUENCE_TYPE_TITLE = "Sequence Type"
MESSAGE_TITLE = "DNAMAN"
