from nicegui import ui


BURGUNDY = "#651D32"
BURGUNDY_DARK = "#40101F"
GOLD = "#C59A54"

STATUS_COLORS = {
    "Strong": "#2E7156",
    "Watch": "#AF7824",
    "At risk": "#A33D45",
}


def apply_theme() -> None:
    ui.add_head_html(
        '''
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap"
              rel="stylesheet">
        '''
    )

    ui.add_css(
        '''
        :root {
            --sw-bg: #F7F3EE;
            --sw-surface: #FFFFFF;
            --sw-surface-soft: #FCF9F5;

            --sw-burgundy: #651D32;
            --sw-burgundy-dark: #40101F;
            --sw-burgundy-soft: #8A3650;

            --sw-gold: #C59A54;
            --sw-gold-soft: #E8D7B4;

            --sw-text: #2B2527;
            --sw-text-soft: #776D70;

            --sw-border: #E7DED5;

            --sw-success: #2E7156;
            --sw-warning: #AF7824;
            --sw-danger: #A33D45;
        }

        body {
            background: var(--sw-bg);
            color: var(--sw-text);
            font-family: 'Inter', sans-serif;
        }

        .q-page {
            background: var(--sw-bg);
        }

        .app-header {
            background: rgba(255, 255, 255, 0.97);
            color: var(--sw-text);
            border-bottom: 1px solid var(--sw-border);
            box-shadow: none;
            min-height: 68px;
        }

        .app-drawer {
            background:
                linear-gradient(
                    180deg,
                    var(--sw-burgundy-dark) 0%,
                    var(--sw-burgundy) 100%
                );
            color: white;
        }

        .brand-title {
            font-family: 'Playfair Display', serif;
            font-size: 21px;
            font-weight: 700;
            letter-spacing: 0.2px;
        }

        .brand-subtitle {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.62);
            letter-spacing: 1.4px;
            text-transform: uppercase;
        }

        .nav-section-label {
            color: rgba(255, 255, 255, 0.48);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.4px;
            text-transform: uppercase;
            margin-top: 18px;
            margin-bottom: 7px;
        }

        .nav-item {
            width: 100%;
            min-height: 46px;
            border-radius: 8px;
            color: rgba(255, 255, 255, 0.78);
            transition: all 0.18s ease;
            cursor: pointer;
            padding-left: 12px;
            padding-right: 12px;
        }

        .nav-item:hover {
            background: rgba(255, 255, 255, 0.08);
            color: white;
        }

        .nav-item-active {
            background: rgba(197, 154, 84, 0.18);
            color: white;
            border-left: 3px solid var(--sw-gold);
        }

        .page-wrapper {
            width: 100%;
            max-width: 1650px;
            margin: 0 auto;
            padding: 30px 34px 50px 34px;
        }

        .page-title {
            font-family: 'Playfair Display', serif;
            font-size: 30px;
            font-weight: 700;
            line-height: 1.2;
            color: var(--sw-burgundy-dark);
        }

        .page-subtitle {
            font-size: 13px;
            color: var(--sw-text-soft);
            margin-top: 5px;
            max-width: 900px;
        }

        .eyebrow {
            color: var(--sw-gold);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.7px;
            text-transform: uppercase;
        }

        .surface-card {
            background: var(--sw-surface);
            border: 1px solid var(--sw-border);
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(62, 32, 39, 0.04);
        }

        .metric-card {
            background: var(--sw-surface);
            border: 1px solid var(--sw-border);
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(62, 32, 39, 0.035);
        }

        .metric-icon {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(101, 29, 50, 0.08);
            color: var(--sw-burgundy);
        }

        .muted {
            color: var(--sw-text-soft);
        }

        .network-map .leaflet-container {
            border-radius: 12px;
        }

        .network-detail {
            background: linear-gradient(155deg, #40101F, #651D32);
            color: white;
            border-radius: 16px;
            box-shadow: 0 16px 38px rgba(64, 16, 31, 0.20);
        }

        .network-table .q-table tbody tr {
            cursor: pointer;
        }

        .network-table .q-table tbody tr.q-tr--selected {
            background: rgba(101, 29, 50, 0.09) !important;
            box-shadow: inset 4px 0 0 var(--sw-burgundy);
        }

        .placeholder-card {
            min-height: 300px;
            background:
                linear-gradient(
                    145deg,
                    var(--sw-surface) 0%,
                    var(--sw-surface-soft) 100%
                );
            border: 1px solid var(--sw-border);
            border-radius: 14px;
            padding: 36px;
        }

        .placeholder-icon {
            width: 52px;
            height: 52px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(101, 29, 50, 0.08);
            color: var(--sw-burgundy);
        }

        .placeholder-title {
            font-family: 'Playfair Display', serif;
            color: var(--sw-burgundy-dark);
            font-size: 21px;
            font-weight: 700;
        }

        .placeholder-text {
            color: var(--sw-text-soft);
            font-size: 13px;
            line-height: 1.7;
            max-width: 650px;
        }

        .version-badge {
            background: #F5EEE4;
            color: var(--sw-burgundy);
            border: 1px solid #E7D9C8;
            border-radius: 20px;
            padding: 5px 10px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .synthetic-badge {
            color: var(--sw-warning);
            background: #FFF8E8;
            border: 1px solid #F0DCA8;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 10px;
            font-weight: 700;
        }

        .section-title {
            font-family: 'Playfair Display', serif;
            color: var(--sw-burgundy-dark);
            font-size: 18px;
            font-weight: 700;
        }
        '''
    )
