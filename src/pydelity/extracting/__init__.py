"""Page extraction: each selected page's items, in reading order, as a page file.

A vision model reads each page from an image of it, and code checks its answer.
When page extraction's verifier is on, a second request to the same model reviews
the page before its file is written.
"""
