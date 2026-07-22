# Section Comparison Summary — C2D-2

| Metric | Value |
|--------|------:|
| Sections compared (union) | 45 |
| Identical content hash | **15** |
| Differing content hash | **30** |

## Differing sections (30)

`.data`, `.data.rel.ro`, `.debug_abbrev`, `.debug_addr`, `.debug_aranges`, `.debug_frame`, `.debug_info`, `.debug_line`, `.debug_macro`, `.debug_ranges`, `.debug_str`, `.dynamic`, `.dynstr`, `.dynsym`, `.eh_frame`, `.eh_frame_hdr`, `.gnu.version`, `.got`, `.got.plt`, `.init`, `.note.gnu.build-id`, `.plt`, `.rela.dyn`, `.rela.plt`, `.relro_padding`, `.rodata`, `.strtab`, `.symtab`, `.tdata`, **`.text`**

## Identical sections (15)

`.bss` (NOBITS size), `.comment`, `.debug_gdb_scripts`, `.debug_loc`, `.fini`, `.fini_array`, `.gcc_except_table`, `.gnu.hash`, `.gnu.version_r`, `.init_array`, `.interp`, `.note.ABI-tag`, `.shstrtab`, `.tbss` (NOBITS size), `.tm_clone_table` (empty)

## Notable size deltas

| Section | Old size | New size | Delta |
|---------|---------:|---------:|------:|
| `.text` | 174369132 | 174406412 | +37280 |
| `.debug_line` | 121700518 | 121327035 | -373483 |
| `.debug_str` | 7365668 | 7516880 | +151212 |
| `.rodata` | 17187960 | 17171576 | -16384 |
| `.rela.dyn` | 27428784 | 27424704 | -4080 |
| file total | 600647920 | 600515304 | **-132616** |

Full hashes: `SECTION_HASH_COMPARISON.csv`
