#!/usr/bin/env python3
"""Generate Portland SE Apartment Search PDF report from listings.json."""

import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image
)

# Colors
DARK_GREEN = HexColor("#2d6a4f")
LIGHT_GREEN = HexColor("#d8f3dc")
DARK_BLUE = HexColor("#1d3557")
LIGHT_BLUE = HexColor("#a8dadc")
HEADER_BG = HexColor("#264653")
ROW_ALT = HexColor("#f1faee")
WHITE = HexColor("#ffffff")
BLACK = HexColor("#000000")
GRAY = HexColor("#6c757d")

def score_listing(listing):
    """Score a listing 0-100 based on the evaluation rubric."""
    score = 0

    # Room count (20%): 2 rooms = 15pts, 3+ rooms = 20pts
    beds = listing.get("bedrooms", 0)
    if beds >= 3:
        score += 20
    elif beds >= 2:
        score += 15

    # Kitchen quality (15%): Full kitchen = 15pts, kitchenette = 10pts
    if listing.get("has_kitchen"):
        score += 15
    elif listing.get("has_kitchenette"):
        score += 10
    else:
        score += 5

    # Powell/Division proximity (20%)
    neighborhood = listing.get("neighborhood", "")
    address = listing.get("address", "").lower()
    # Close to Powell/Division corridors
    if any(k in address for k in ["powell", "division", "holgate"]):
        score += 20
    elif neighborhood in ["Hosford-Abernethy", "Creston-Kenilworth", "Brooklyn"]:
        score += 15
    elif neighborhood in ["Buckman", "Richmond", "Sunnyside"]:
        score += 10
    else:
        score += 5

    # Price reasonableness (15%)
    price = listing.get("price", 9999)
    if price < 1800:
        score += 15
    elif price < 2200:
        score += 12
    elif price < 2800:
        score += 8
    elif price < 3500:
        score += 5
    else:
        score += 3

    # Square footage (10%)
    sqft = listing.get("sqft")
    if sqft and sqft > 900:
        score += 10
    elif sqft and sqft > 700:
        score += 7
    elif sqft and sqft > 500:
        score += 4
    else:
        score += 2  # Unknown sqft gets minimal score

    # Mixed-use friendliness (10%)
    desc = listing.get("description_excerpt", "").lower()
    amenities_str = " ".join(listing.get("amenities", [])).lower()
    combined = desc + " " + amenities_str
    if any(k in combined for k in ["live/work", "mixed use", "home office", "commercial"]):
        score += 10
    elif any(k in combined for k in ["townhouse", "individual entrance", "flex"]):
        score += 7
    elif any(k in combined for k in ["ground floor", "creative", "loft"]):
        score += 5
    else:
        score += 3

    # Fiber internet (10%)
    internet = listing.get("internet", {})
    classification = internet.get("classification", "")
    if classification == "Excellent":
        score += 10
    elif classification == "Good":
        score += 5
    elif classification == "Adequate":
        score += 3
    else:
        score += 0

    return score

def build_pdf(listings, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=DARK_BLUE,
        spaceAfter=6,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=GRAY,
        spaceAfter=20,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=DARK_BLUE,
        spaceBefore=16,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        'ListingTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=DARK_GREEN,
        spaceBefore=12,
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'DetailLabel',
        parent=styles['Normal'],
        fontSize=10,
        textColor=GRAY,
        spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        'DetailValue',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=GRAY,
        spaceAfter=2
    ))

    story = []

    # Title page
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph(
        "Portland SE Apartment Search",
        styles['ReportTitle']
    ))
    story.append(Paragraph(
        "Live/Work Space Report",
        styles['ReportTitle']
    ))
    story.append(Spacer(1, 12))
    now = datetime.now()
    story.append(Paragraph(
        now.strftime("%B %d, %Y at %I:%M %p"),
        styles['ReportSubtitle']
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Inner SE Portland | Powell &amp; Division Corridors",
        styles['ReportSubtitle']
    ))
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="60%", color=DARK_BLUE, thickness=2))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Target: 2+ bedroom apartments with kitchen, suitable for live/work use, "
        "with reliable fiber internet connectivity.",
        styles['Normal']
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Source: Craigslist Portland | Internet: BroadbandNow (address-specific)",
        styles['SmallText']
    ))
    story.append(PageBreak())

    # Score all listings
    scored = []
    for l in listings:
        s = score_listing(l)
        scored.append((s, l))
    scored.sort(key=lambda x: x[0], reverse=True)

    # Summary table
    story.append(Paragraph("Summary Rankings", styles['SectionHeader']))
    story.append(Spacer(1, 6))

    table_data = [["Rank", "Address", "Neighborhood", "Price", "Beds/Bath", "Internet", "Score"]]
    for i, (sc, l) in enumerate(scored, 1):
        short_addr = l["address"].replace(", Portland, OR ", "\n").replace("97202", "97202").replace("97214", "97214")
        table_data.append([
            str(i),
            Paragraph(l["address"].split(",")[0], styles['SmallText']),
            l["neighborhood"],
            f"${l['price']:,}",
            f"{l['bedrooms']}BR/{l['bathrooms']}BA",
            l["internet"]["classification"],
            f"{sc}/100"
        ])

    summary_table = Table(table_data, colWidths=[0.4*inch, 1.8*inch, 1.2*inch, 0.7*inch, 0.8*inch, 0.8*inch, 0.6*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Detailed listings
    story.append(Paragraph("Detailed Listings", styles['SectionHeader']))
    story.append(HRFlowable(width="100%", color=DARK_BLUE, thickness=1))

    for rank, (sc, l) in enumerate(scored, 1):
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            f"#{rank} - {l['address'].split(',')[0]}",
            styles['ListingTitle']
        ))
        story.append(Paragraph(
            f"{l['neighborhood']} | ${l['price']:,}/mo | {l['bedrooms']}BR/{l['bathrooms']}BA"
            + (f" | {l['sqft']} sqft" if l.get('sqft') else ""),
            styles['DetailLabel']
        ))
        story.append(Spacer(1, 4))

        # Listing photo gallery
        screenshot_dir = os.path.join(os.path.dirname(output_path), "screenshots")
        photos = []
        for i in range(1, 5):
            p = os.path.join(screenshot_dir, f"{l['id']}-{i}.jpg")
            if os.path.exists(p):
                photos.append(p)
        # Fallback: check for old single-photo format
        if not photos:
            single = os.path.join(screenshot_dir, f"{l['id']}.jpg")
            if os.path.exists(single):
                photos.append(single)

        if len(photos) == 1:
            img = Image(photos[0], width=5*inch, height=3.75*inch)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 6))
        elif len(photos) >= 2:
            cell_w = 2.45 * inch
            cell_h = 1.84 * inch
            imgs = [Image(p, width=cell_w, height=cell_h) for p in photos[:4]]
            if len(imgs) == 2:
                grid_data = [[imgs[0], imgs[1]]]
            elif len(imgs) == 3:
                grid_data = [[imgs[0], imgs[1]], [imgs[2], ""]]
            else:
                grid_data = [[imgs[0], imgs[1]], [imgs[2], imgs[3]]]
            gallery = Table(grid_data, colWidths=[cell_w + 6, cell_w + 6], rowHeights=[cell_h + 6] * len(grid_data))
            gallery.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dee2e6")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]))
            gallery.hAlign = 'CENTER'
            story.append(gallery)
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(
                "<i>(Photos unavailable)</i>",
                styles['SmallText']
            ))
            story.append(Spacer(1, 4))

        # Description
        story.append(Paragraph(
            f"<b>Description:</b> {l['description_excerpt']}",
            styles['DetailValue']
        ))

        # Amenities
        amenities_str = ", ".join(l.get("amenities", []))
        story.append(Paragraph(
            f"<b>Amenities:</b> {amenities_str}",
            styles['DetailValue']
        ))

        # Internet
        inet = l.get("internet", {})
        story.append(Paragraph(
            f"<b>Internet ({inet.get('classification', 'N/A')}):</b> "
            f"{inet.get('broadbandnow_summary', 'No data')}",
            styles['DetailValue']
        ))

        # Score breakdown
        beds = l.get("bedrooms", 0)
        room_score = 20 if beds >= 3 else 15
        kitchen_score = 15 if l.get("has_kitchen") else (10 if l.get("has_kitchenette") else 5)

        neighborhood = l.get("neighborhood", "")
        address = l.get("address", "").lower()
        if any(k in address for k in ["powell", "division", "holgate"]):
            prox_score = 20
        elif neighborhood in ["Hosford-Abernethy", "Creston-Kenilworth", "Brooklyn"]:
            prox_score = 15
        elif neighborhood in ["Buckman", "Richmond", "Sunnyside"]:
            prox_score = 10
        else:
            prox_score = 5

        price = l.get("price", 9999)
        if price < 1800: price_score = 15
        elif price < 2200: price_score = 12
        elif price < 2800: price_score = 8
        elif price < 3500: price_score = 5
        else: price_score = 3

        sqft = l.get("sqft")
        if sqft and sqft > 900: sqft_score = 10
        elif sqft and sqft > 700: sqft_score = 7
        elif sqft and sqft > 500: sqft_score = 4
        else: sqft_score = 2

        desc_lower = l.get("description_excerpt", "").lower()
        amen_lower = " ".join(l.get("amenities", [])).lower()
        combined = desc_lower + " " + amen_lower
        if any(k in combined for k in ["live/work", "mixed use", "home office"]): mixed_score = 10
        elif any(k in combined for k in ["townhouse", "individual entrance", "flex"]): mixed_score = 7
        elif any(k in combined for k in ["ground floor", "creative", "loft"]): mixed_score = 5
        else: mixed_score = 3

        classification = inet.get("classification", "")
        if classification == "Excellent": inet_score = 10
        elif classification == "Good": inet_score = 5
        else: inet_score = 0

        score_data = [
            ["Factor", "Weight", "Score", "Max"],
            ["Room Count", "20%", str(room_score), "20"],
            ["Kitchen Quality", "15%", str(kitchen_score), "15"],
            ["Powell/Division Proximity", "20%", str(prox_score), "20"],
            ["Price Reasonableness", "15%", str(price_score), "15"],
            ["Square Footage", "10%", str(sqft_score), "10"],
            ["Mixed-Use Friendliness", "10%", str(mixed_score), "10"],
            ["Fiber Internet", "10%", str(inet_score), "10"],
            ["TOTAL", "100%", str(sc), "100"],
        ]
        score_table = Table(score_data, colWidths=[2*inch, 0.7*inch, 0.6*inch, 0.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), DARK_GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [WHITE, ROW_ALT]),
            ('BACKGROUND', (0, -1), (-1, -1), LIGHT_GREEN),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(Spacer(1, 6))
        story.append(score_table)

        # Link
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f'<a href="{l["url"]}" color="blue">View listing on Craigslist</a>',
            styles['SmallText']
        ))
        story.append(HRFlowable(width="100%", color=HexColor("#dee2e6"), thickness=0.5))

    # Methodology page
    story.append(PageBreak())
    story.append(Paragraph("Methodology", styles['SectionHeader']))
    story.append(HRFlowable(width="100%", color=DARK_BLUE, thickness=1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Data Sources</b>", styles['Normal']))
    story.append(Paragraph(
        "Listings were sourced from Craigslist Portland (apartments/housing for rent), "
        "filtered to 2+ bedrooms within a 3-mile radius of zip code 97202 in Inner SE Portland.",
        styles['DetailValue']
    ))
    story.append(Paragraph(
        "Internet availability was checked at each specific street address using BroadbandNow.com's "
        "address-level lookup tool, which queries provider coverage databases via Google Places autocomplete.",
        styles['DetailValue']
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Scoring Rubric (0-100 scale)</b>", styles['Normal']))
    rubric_data = [
        ["Factor", "Weight", "Criteria"],
        ["Room Count", "20%", "2 rooms = 15pts, 3+ rooms = 20pts"],
        ["Kitchen Quality", "15%", "Full kitchen = 15pts, kitchenette = 10pts"],
        ["Powell/Division\nProximity", "20%", "On corridor = 20pts, adjacent neighborhood = 15pts, nearby = 10pts"],
        ["Price", "15%", "<$1,800 = 15pts, $1,800-2,200 = 12pts, $2,200-2,800 = 8pts"],
        ["Square Footage", "10%", ">900 sqft = 10pts, 700-900 = 7pts, <700 = 4pts, unknown = 2pts"],
        ["Mixed-Use\nFriendliness", "10%", "Live/work keywords = 10pts, townhouse = 7pts, none = 3pts"],
        ["Fiber Internet", "10%", "Excellent (fiber) = 10pts, Good (cable) = 5pts"],
    ]
    rubric_table = Table(rubric_data, colWidths=[1.3*inch, 0.6*inch, 4.3*inch])
    rubric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(Spacer(1, 4))
    story.append(rubric_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Target Neighborhoods</b>", styles['Normal']))
    story.append(Paragraph(
        "Hosford-Abernethy, Richmond, Creston-Kenilworth, Brooklyn, Buckman, and Sunnyside "
        "in Inner SE Portland, along the Powell Blvd and Division St corridors.",
        styles['DetailValue']
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Internet Classification</b>", styles['Normal']))
    story.append(Paragraph(
        "Excellent: Residential fiber available (Quantum Fiber or CenturyLink, 940+ Mbps symmetric). "
        "Good: Gigabit cable available (Xfinity 2 Gbps) but no residential fiber at specific address. "
        "Adequate: Cable under 500 Mbps. Poor: DSL only.",
        styles['DetailValue']
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        f"Report generated {now.strftime('%B %d, %Y at %I:%M %p')}. Data may change; verify listings and internet availability before signing a lease.",
        styles['SmallText']
    ))

    doc.build(story)
    print(f"PDF generated: {output_path}")

if __name__ == "__main__":
    with open("/Users/dit/github/cowork-aparmentsearch/data/output/listings.json") as f:
        listings = json.load(f)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    output_path = f"/Users/dit/github/cowork-aparmentsearch/data/output/portland-apartment-report-{timestamp}.pdf"
    build_pdf(listings, output_path)
