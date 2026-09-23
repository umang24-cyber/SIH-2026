import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "BITKAUN V8 FORENSIC ENGINE // OFFICIAL COMMAND & ID REFERENCE")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "CONFIDENTIAL // SMART INDIA HACKATHON 2026 // AIR-GAPPED FORENSICS")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

def build_pdf(filename="BitKaun_Command_Reference_CheatSheet.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=44,
        rightMargin=44,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a")
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569")
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    cmd_name_style = ParagraphStyle(
        'CmdName',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0284c7")
    )
    
    code_style = ParagraphStyle(
        'CodeText',
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f766e")
    )
    
    desc_style = ParagraphStyle(
        'DescText',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )
    
    th_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    
    story = []
    
    # Title Banner
    story.append(Paragraph("BITKAUN V8 FORENSICS // COMMAND & ID CHEAT SHEET", title_style))
    story.append(Paragraph("Smart India Hackathon 2026 • Air-Gapped Dual-Stream Bitcoin AML Forensics Engine<br/>Verified Working Invocations across OS CLI (Ubuntu WSL / Windows) and Web Terminal", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))
    
    # Overview Banner Box
    meta_data = [
        [
            Paragraph("<b>Target Backend:</b> http://localhost:8000", desc_style),
            Paragraph("<b>Indexed Tx Count:</b> 294,717 Transactions", desc_style),
            Paragraph("<b>AI Models:</b> XGBoost + Isolation Forest", desc_style)
        ],
        [
            Paragraph("<b>Web Terminal:</b> http://localhost:5173", desc_style),
            Paragraph("<b>Unique Wallets:</b> 984,132 Addresses", desc_style),
            Paragraph("<b>Case Storage:</b> %LOCALAPPDATA%\\BitKaun", desc_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[170, 170, 174])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))
    
    # Table of Commands with 2 verified working IDs
    commands_data = [
        # Headers
        [
            Paragraph("Command & Syntax", th_style),
            Paragraph("Working ID / Invocations (2 Verified Examples)", th_style),
            Paragraph("Forensic Purpose & Demonstrated Output", th_style)
        ],
        # 1. search
        [
            Paragraph("<b>search</b><br/><font size=7.5 color='#64748b'>search &lt;query&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>search AS49870</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>search 152.60.31.67</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Unmasks all mixing relay nodes operating under ASN 49870.<br/>"
                "<b>2.</b> Unmasks origin node (Residential, SC, 482 ms propagation latency).",
                desc_style
            )
        ],
        # 2. correlate
        [
            Paragraph("<b>correlate</b><br/><font size=7.5 color='#64748b'>correlate | upload</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>correlate</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>ingest sample-pair</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Opens Dual-Stream Ledger & P2P Telemetry correlation view in Web UI.<br/>"
                "<b>2.</b> Correlates 100 on-chain UTXO rows with P2P frames; runs instant SHAP scoring.",
                desc_style
            )
        ],
        # 3. inspect
        [
            Paragraph("<b>inspect</b><br/><font size=7.5 color='#64748b'>inspect &lt;txid|addr&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>inspect 932451115</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>inspect 881920041</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Massive 10,034 BTC peeling tx, 1-in 2-out, Green Floid LLC ISP.<br/>"
                "<b>2.</b> Ransomware extortion payment with multi-party victim consolidation.",
                desc_style
            )
        ],
        # 4. dossier
        [
            Paragraph("<b>dossier</b><br/><font size=7.5 color='#64748b'>dossier &lt;txid&gt; [--save]</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>dossier 932451115 --save</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>dossier 881920041 --save</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Generates FIU-IND prosecution summary; saves JSON to active case.<br/>"
                "<b>2.</b> Section 65B court evidence package for ransomware syndicate.",
                desc_style
            )
        ],
        # 5. flow
        [
            Paragraph("<b>flow</b><br/><font size=7.5 color='#64748b'>flow &lt;txid&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>flow 932451115</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>flow 324013641</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Decomposes peeling split: 10,034 BTC into change address and peel hop.<br/>"
                "<b>2.</b> Decomposes CoinJoin mixer pool: multi-input equal-split distribution.",
                desc_style
            )
        ],
        # 6. anomaly
        [
            Paragraph("<b>anomaly</b><br/><font size=7.5 color='#64748b'>anomaly &lt;scenario_id&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>anomaly mixing_05121</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>anomaly peeling_chain_04606</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Isolation Forest score: <b>58.18 / 100 [MEDIUM]</b> (Raw: -0.5154).<br/>"
                "<b>2.</b> Isolation Forest score: <b>74.24 / 100 [HIGH]</b> unusualness deviation.",
                desc_style
            )
        ],
        # 7. graph
        [
            Paragraph("<b>graph</b><br/><font size=7.5 color='#64748b'>graph &lt;scenario_id&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>graph peeling_chain_04606</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>graph mixing_05121</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Web UI: 3D WebGL camera focuses on linear peeling chain trail.<br/>"
                "<b>2.</b> CLI: Prints node/edge counts & hub wallets for CoinJoin mixing pool.",
                desc_style
            )
        ],
        # 8. communities
        [
            Paragraph("<b>communities</b><br/><font size=7.5 color='#64748b'>communities &lt;scenario_id&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>communities peeling_chain_04601</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>communities mixing_05121</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Greedy Modularity detects coordinator vs change wallet syndicates.<br/>"
                "<b>2.</b> Separates pre-mix depositor clusters from post-mix clean recipients.",
                desc_style
            )
        ],
        # 9. taint
        [
            Paragraph("<b>taint</b><br/><font size=7.5 color='#64748b'>taint &lt;seed_address&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>taint 14c55RuJwJivdZmEjpTDJNjcAfvLdkaH</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>taint 1c9Tm1sAir7vV5mn7e3zZwo6eDZZd16RHz</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Computes forward dirty coin decay from peeling syndicate master head.<br/>"
                "<b>2.</b> Mathematical FIFO taint propagation across downstream change wallets.",
                desc_style
            )
        ],
        # 10. trace
        [
            Paragraph("<b>trace</b><br/><font size=7.5 color='#64748b'>trace &lt;src&gt; &lt;dst&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>trace 1c9Tm1sAir7vV5mn7e3zZwo6eDZZd16RHz 1Cc18UpLkcS5FcZsKuPxKWpv1fT</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>trace 1Vo1CYJGZqnHYk2TKjNiuaWkTZgZ47n 1cUUSwM6WHg23QmLUxPGdWWY2XHzL68W4</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Multi-hop BFS velocity trace across peeling chain 04601.<br/>"
                "<b>2.</b> Direct fund routing path across peeling chain 04602 to cashout exit.",
                desc_style
            )
        ],
        # 11. tor
        [
            Paragraph("<b>tor</b><br/><font size=7.5 color='#64748b'>tor [txid]</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>tor 932451115</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>tor 324013641</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Shannon timing entropy test: Tor Negative, 482 ms Clearnet propagation.<br/>"
                "<b>2.</b> Evaluates gossip broadcast delay and timing jitter for mixer node.",
                desc_style
            )
        ],
        # 12. ingest
        [
            Paragraph("<b>ingest</b><br/><font size=7.5 color='#64748b'>ingest sample &lt;type&gt;</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>ingest sample peeling</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>ingest sample ransomware</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Injects synthetic peeling chain with instant real-time XGBoost ML scoring.<br/>"
                "<b>2.</b> Injects high-threat extortion transaction into live in-memory graph.",
                desc_style
            )
        ],
        # 13. scenarios
        [
            Paragraph("<b>scenarios</b><br/><font size=7.5 color='#64748b'>scenarios [prefix] [page]</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>scenarios peel 1</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>scenarios mix 1</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Paginated directory filtering all active peeling chain clusters.<br/>"
                "<b>2.</b> Directory of all CoinJoin / Wasabi mixing scenario clusters.",
                desc_style
            )
        ],
        # 14. cases & cd
        [
            Paragraph("<b>cases / cd</b><br/><font size=7.5 color='#64748b'>cases | cd &lt;case&gt; | cd ..</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>cases</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>cd test3</font> (Exit: <font face='Courier-Bold' color='#0f766e'>cd ..</font>)",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> Lists all cases stored in private local AppData with artifact counts.<br/>"
                "<b>2.</b> Activates case 'test3' for evidence isolation. 'cd ..' returns to global.",
                desc_style
            )
        ],
        # 15. benchmark & telemetry
        [
            Paragraph("<b>benchmark / telemetry</b><br/><font size=7.5 color='#64748b'>benchmark | telemetry</font>", cmd_name_style),
            Paragraph(
                "<b>1.</b> <font face='Courier-Bold' color='#0f766e'>benchmark</font><br/>"
                "<b>2.</b> <font face='Courier-Bold' color='#0f766e'>telemetry</font>",
                desc_style
            ),
            Paragraph(
                "<b>1.</b> V8 Frozen Scorecard: <b>93.9% F1</b>, <b>0.42 ms</b> sub-millisecond AI latency.<br/>"
                "<b>2.</b> Global P2P infrastructure census: Tor vs Residential vs Datacenter nodes.",
                desc_style
            )
        ]
    ]
    
    t_cmd = Table(commands_data, colWidths=[110, 230, 174])
    t_cmd.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(t_cmd)
    story.append(Spacer(1, 14))
    
    # Bottom Callout Box: Hackathon Pitch Cheat Sheet
    story.append(Paragraph("<b>HACKATHON PRESENTATION & EVALUATION CHEAT SHEET (SIH 2026)</b>", h1_style))
    tips_data = [
        [
            Paragraph(
                "<b>1. Latency Breakdown:</b> AI ML Inference is <b>0.42 ms</b> (420 microseconds) per transaction. P2P propagation latency is <b>&lt;500 ms</b> on clearnet vs <b>800–8,500 ms</b> on Tor relays.<br/>"
                "<b>2. Why Models Don't Self-Learn Online:</b> Prevents adversarial poisoning by criminals and guarantees court admissibility under Section 65B of the Indian Evidence Act with a certified frozen benchmark version.<br/>"
                "<b>3. Dual-Stream Fusion:</b> BitKaun does not just look at on-chain UTXO graphs; it fuses pre-block Layer-0 gossip network telemetry (Relay IP, ASN, Tor exit status) with on-chain ledgers.<br/>"
                "<b>4. Flexible Schema Ingestion:</b> Supports user CSV uploads with arbitrary headers (e.g. <i>From_Address, TxHash, Value</i>) auto-mapped with zero manual formatting.",
                desc_style
            )
        ]
    ]
    t_tips = Table(tips_data, colWidths=[514])
    t_tips.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#3b82f6")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_tips)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Successfully generated: {filename}")

if __name__ == "__main__":
    build_pdf()
