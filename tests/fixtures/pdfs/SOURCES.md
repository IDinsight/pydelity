# Test PDFs

These are real documents that pydelity's tests use. Each one is free of
copyright under the law named in its entry, and each is under 500 KB. The size
and SHA-256 identify the exact file, so a test can tell if a file changed.

## bls_navigating_slides.pdf

- Source:
  [Navigating the Bureau of Labor Statistics](https://fdlp.gov/sites/default/files/training/20220830-wn-navigating-bureau-labor-statistics-slides.pdf),
  a training slide deck by U.S. Bureau of Labor Statistics staff (2022),
  published by the U.S. Government Publishing Office's Federal Depository
  Library Program.
- License basis: a work of the U.S. federal government, which has no copyright
  in the United States (17 U.S.C. § 105).
- Size: 386,617 bytes, 16 pages.
- SHA-256: `0956fb9fd32e1e0a0c7207b54e307f33afaea4f516f326c8cf0e11dbbe6b2c69`
- Contains: a slide deck exported from PowerPoint (720 × 540 point pages) with
  two or three images on every slide; tagged.

## caps_english_hl_pages_28_35.pdf

- Source: pages 28–35 of the _Curriculum and Assessment Policy Statement (CAPS):
  English Home Language, Grades R–3_ (142 pages, © 2011 Department of Basic
  Education, South Africa), published at
  [education.gov.za](https://www.education.gov.za). The pages were copied into a
  new PDF with PyMuPDF, keeping the original printed page labels (23–30).
- License basis: South Africa's Copyright Act 98 of 1978, section 12(8)(a),
  under which no copyright subsists in official texts of a legislative,
  administrative or legal nature. CAPS is the national curriculum policy.
- Size: 167,626 bytes, 8 pages.
- SHA-256: `8191739d1ad6277ee77f7473b460699419d76a6b44c74794fd82b5929aa93985`
- Contains: landscape tables printed sideways on portrait pages whose rotation
  attribute is 0 (88–98% of each page's text runs top to bottom); page labels;
  no tags or bookmarks.

## irs_form_1040_1950.pdf

- Source:
  [U.S. Individual Income Tax Return, Form 1040 (1950)](https://www.irs.gov/pub/irs-prior/f1040--1950.pdf),
  Internal Revenue Service.
- License basis: a work of the U.S. federal government (17 U.S.C. § 105).
- Size: 69,774 bytes, 4 pages.
- SHA-256: `f13c2414dd1754e8ea12d9d7150d7834fdcc4a7a2ebd94c460351d64297b80be`
- Contains: a typed text layer; page labels; a tax table on page 4 whose column
  headings run sideways on a page with rotation attribute 0; no tags or
  bookmarks.

## irs_form_1040a_1965_scan.pdf

- Source:
  [U.S. Individual Income Tax Return, Form 1040A (1965)](https://www.irs.gov/pub/irs-prior/f1040a--1965.pdf),
  Internal Revenue Service.
- License basis: a work of the U.S. federal government (17 U.S.C. § 105).
- Size: 85,909 bytes, 2 pages.
- SHA-256: `a0efe68d8c1e066684f9aa89e73cc0931f83b7713e0d8f45b0bf1a8bdddf9169`
- Contains: scanned pages, one image each, with no text layer; no tags or
  bookmarks.

## irs_form_w9.pdf

- Source:
  [Form W-9, Request for Taxpayer Identification Number and Certification (Rev. March 2024)](https://www.irs.gov/pub/irs-pdf/fw9.pdf),
  Internal Revenue Service.
- License basis: a work of the U.S. federal government (17 U.S.C. § 105).
- Size: 140,815 bytes, 6 pages.
- SHA-256: `2d420cbb4123dcf1fb82595b2359cfbb5d81f00b9df9d359fcc7af361d093f53`
- Contains: a fillable form with 8 checkboxes and 15 text fields, plus an XFA
  form; tagged; a short line of sideways text on page 1, whose rotation
  attribute is 0.

## irs_pub1_arabic.pdf

- Source:
  [Publication 1 (AR), Your Rights as a Taxpayer (Rev. 9-2017)](https://www.irs.gov/pub/irs-pdf/p1ar.pdf),
  Internal Revenue Service.
- License basis: a work of the U.S. federal government (17 U.S.C. § 105).
- Size: 115,120 bytes, 2 pages.
- SHA-256: `3bf73157c5170446af9d66afe6d4fa44de7997313117b3e8f04b832c524759db`
- Contains: Arabic text (right to left) in two columns on page 1 and three on
  page 2; tagged; no bookmarks.

## irs_pub1_chinese_simplified.pdf

- Source:
  [Publication 1 (ZH-S), Your Rights as a Taxpayer (Rev. 9-2017)](https://www.irs.gov/pub/irs-pdf/p1zhs.pdf),
  Internal Revenue Service.
- License basis: a work of the U.S. federal government (17 U.S.C. § 105).
- Size: 164,978 bytes, 2 pages.
- SHA-256: `ddc9463616f224865e2dd60637fd03869572a4f04d7ac55f7fa863cef9da446e`
- Contains: Simplified Chinese text in two and three columns; tagged; no
  bookmarks.

## irs_w9_instructions.pdf

- Source:
  [Instructions for the Requester of Form W-9 (Rev. March 2024)](https://www.irs.gov/pub/irs-pdf/iw9.pdf),
  Internal Revenue Service.
- License basis: a work of the U.S. federal government (17 U.S.C. § 105).
- Size: 189,808 bytes, 7 pages.
- SHA-256: `ec609a8bf9fac7da593355a57e49e0aa4d569eaceca3a7a84255104d864b1c34`
- Contains: two-column English text; 22 bookmarks; tagged.

## irs_w9_instructions_rotated.pdf

- Source: a copy of `irs_w9_instructions.pdf` above, with the rotation attribute
  of pages 2, 3 and 4 set to 90, 180 and 270 degrees. Nothing else changed:
  every page's text is the same, and the bookmarks and tags are kept.
- Made with PyMuPDF 2.1, at the repository root:

  ```python
  import pymupdf

  document = pymupdf.open("tests/fixtures/pdfs/irs_w9_instructions.pdf")
  for index, degrees in {1: 90, 2: 180, 3: 270}.items():
      document[index].set_rotation(degrees)
  document.save(
      "tests/fixtures/pdfs/irs_w9_instructions_rotated.pdf",
      deflate=True,
      garbage=1,
      use_objstms=1,
  )
  ```

  Running it again gives the same pages but not the same bytes, because PyMuPDF
  writes a new second part of the file ID each time.

- License basis: as for `irs_w9_instructions.pdf`, a work of the U.S. federal
  government (17 U.S.C. § 105).
- Size: 187,076 bytes, 7 pages.
- SHA-256: `26db71ee9721c68aff804acfc0ee8db983130e50d91733b6fb48dc22a018144c`
- Contains: two-column English text on pages displayed upright (1, 5 to 7),
  turned a quarter clockwise (2), upside down (3) and turned a quarter
  counterclockwise (4); 22 bookmarks; tagged.

## japan_official_gazette_2019_extra_9.pdf

- Source: Japan's Official Gazette (官報), Extra Special No. 9 of 2019 (April 1,
  2019), which announced the Reiwa era name, from
  [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Japanese_Official_Gazette_Extra_Special_No._9_of_2019.pdf).
- License basis: Japan's Copyright Act, Article 13, under which laws, cabinet
  orders and notices of the national government are not subject to copyright.
- Size: 91,173 bytes, 1 page.
- SHA-256: `1a2ad518ecb20a30c02ddcd38b6ea5d75dcd45bce628f7eaa1fbf144371fe13e`
- Contains: Japanese text, mostly in vertical (top-to-bottom) writing; page
  labels; a signature field; no tags or bookmarks.
