"""Build the two demo PDFs. Everything in them is INVENTED: names, places, parcel, amounts.

sale-agreement.pdf       6 pages. 1-3 have a text layer. 4-5 are scans. 6 is a scan lying on its side,
                         and it is the only page that carries the tax figure.
sale-agreement-damaged.pdf  the same, but page 6 is too degraded to read.
"""
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
W, H = 2550, 3300  # US letter at 300 dpi

PAGES = {
 1: ["AGREEMENT FOR THE SALE OF REAL PROPERTY", "",
     "This Agreement is made on the 14th day of March 2025 between",
     "Marrow Creek Holdings, Inc. (the Seller) and Tallow Ridge",
     "Partners LLC (the Buyer).", "",
     "1. PROPERTY. The Seller agrees to sell and the Buyer agrees to",
     "buy the parcel known as 41 Fennel Road, Ashby County, containing",
     "12.40 acres, parcel number 7731-02-118 (the Property).", "",
     "2. PRICE. The purchase price is Four Hundred Ten Thousand",
     "Dollars ($410,000), payable at closing.", "",
     "3. DEPOSIT. The Buyer has paid a deposit of $20,000 to the",
     "escrow agent, to be credited against the price at closing."],
 2: ["4. CLOSING. Closing shall take place on or before 30 June 2025",
     "at the offices of the escrow agent.", "",
     "5. TITLE. The Seller shall convey good and marketable title by",
     "general warranty deed, free of liens except those listed in",
     "the Schedule attached to this Agreement.", "",
     "6. INSPECTION. The Buyer may inspect the Property for thirty",
     "days from the date of this Agreement and may withdraw within",
     "that period, in which case the deposit shall be returned."],
 3: ["7. DEFAULT. If the Buyer fails to close for any reason other",
     "than the Seller's default, the Seller shall keep the deposit",
     "as its only remedy.", "",
     "8. NOTICES. Notices to the Seller shall be sent to the address",
     "of its registered agent. Notices to the Buyer shall be sent to",
     "its office at 9 Quarry Lane, Ashby.", "",
     "9. ENTIRE AGREEMENT. This Agreement and its attachments are the",
     "whole agreement between the parties."],
 4: ["SCHEDULE OF PERMITTED LIENS", "",
     "The following matters are permitted exceptions to title:", "",
     "(a) Utility easement recorded in Book 212 at Page 40.",
     "(b) Right of way for Fennel Road as shown on the county plat.",
     "(c) Restrictions of record that do not prevent the present use.", "",
     "No mortgage, judgment or mechanics lien is a permitted",
     "exception, and each shall be paid by the Seller at closing."],
 5: ["SIGNATURES", "",
     "Signed for the Seller, Marrow Creek Holdings, Inc.", "",
     "By: Orrin Vale, Authorized Signatory", "",
     "Signed for the Buyer, Tallow Ridge Partners LLC", "",
     "By: Hester Lind, Managing Member", "",
     "Witnessed on the 14th day of March 2025."],
 6: ["ADDENDUM No. 1 TO THE AGREEMENT", "",
     "Added by the parties on the 2nd day of April 2025.", "",
     "A. UNPAID TAXES. Property taxes for the years 2022, 2023 and",
     "2024 remain unpaid in the total amount of $18,450. The Seller",
     "shall pay this amount in full before closing.", "",
     "B. PRICE REDUCTION. If the Seller has not paid the unpaid",
     "taxes by closing, the Buyer may deduct $18,450 from the price",
     "and pay the county directly.", "",
     "C. All other terms of the Agreement remain unchanged."],
}


def text_page(c, lines):
    c.setFont("Times-Roman", 13)
    y = 720
    for ln in lines:
        c.drawString(72, y, ln)
        y -= 22
    c.showPage()


def scan_page(lines, sideways=False, damaged=False, seed=1):
    rnd = random.Random(seed)
    img = Image.new("L", (W, H), 250)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 62)
    y = 420
    for ln in lines:
        d.text((300, y), ln, font=font, fill=25)
        y += 104
    img = img.rotate(rnd.uniform(-0.6, 0.6), fillcolor=250)        # a scanner is never square
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    px = img.load()
    for _ in range(9000):                                           # specks
        px[rnd.randrange(W), rnd.randrange(H)] = rnd.randrange(60, 200)
    if damaged:                                                     # a fax of a photocopy of a fax
        img = img.resize((W // 14, H // 14)).resize((W, H)).filter(ImageFilter.GaussianBlur(9))
    if sideways:
        img = img.rotate(90, expand=True)
    return img.convert("RGB")


def build(name, damaged_last):
    parts = []
    first = os.path.join(HERE, "_text.pdf")
    c = canvas.Canvas(first, pagesize=letter)
    for n in (1, 2, 3):
        text_page(c, PAGES[n])
    c.save()
    parts.append(first)
    for n in (4, 5, 6):
        out = os.path.join(HERE, "_scan%d.pdf" % n)
        scan_page(PAGES[n], sideways=(n == 6), damaged=(n == 6 and damaged_last), seed=n).save(out, "PDF", resolution=300.0)
        parts.append(out)
    target = os.path.join(HERE, name)
    subprocess.run(["pdfunite"] + parts + [target], check=True)
    for p in parts:
        os.remove(p)
    for stale in (target + ".everypage.json",):
        if os.path.exists(stale):
            os.remove(stale)
    return target


if __name__ == "__main__":
    print(build("sale-agreement.pdf", False))
    print(build("sale-agreement-damaged.pdf", True))
