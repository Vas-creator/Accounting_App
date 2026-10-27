# core/pdf_generator.py
import os
import json
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from core import db

from weasyprint import HTML, CSS

from core.utils import (
    format_number, format_date_mm, parse_number
)
from core.templates import merge_template_with_data

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_REGULAR = os.path.join(BASE_DIR, "assets", "fonts", "pyidaungsu-regular.ttf")
FONT_BOLD = os.path.join(BASE_DIR, "assets", "fonts", "pyidaungsu-bold.ttf")

# ============================================================
# PDF TRANSLATIONS
# ============================================================
PDF_TRANSLATIONS = {
    "my": {
        "period_end": "ကာလကုန်",
        "as_at_date": "ရက်စွဲ",
        "manufacturing_title": "ကုန်ထုတ်လုပ်မှု စာရင်း (Manufacturing Account)",
        "trading_pl_title": "အရောင်းအဝယ် အမြတ်အစွန်း စာရင်း (Trading & P&L)",
        "balance_sheet_title": "ငွေစာရင်း လက်ကျန်စာရင်း (Balance Sheet)",
        "cash_flow_title": "ငွေသား စီးဆင်းမှု ရှင်းတမ်း (Cash Flow Statement)",

        "m1": "၁။ တိုက်ရိုက် ကုန်ကြမ်းများ",
        "opening_stock_raw": "အဖွင့် ကုန်ကြမ်းလက်ကျန်",
        "purchases_raw": "ကုန်ကြမ်းဝယ်ယူမှု",
        "carriage_inward": "သယ်ယူပို့ဆောင်ခ",
        "customs_duty": "အကောက်ခွန်",
        "closing_stock_raw": "အပိတ် ကုန်ကြမ်းလက်ကျန်",
        "cost_of_materials_used": "အသုံးပြုသော ကုန်ကြမ်းကုန်ကျစရိတ်",
        "m2": "၂။ တိုက်ရိုက် အလုပ်သမားခ",
        "wages_direct": "တိုက်ရိုက် အလုပ်သမားခ",
        "wages_overtime": "အချိန်ပို အလုပ်သမားခ",
        "wages_contract": "စာချုပ် အလုပ်သမားခ",
        "direct_labour_total": "တိုက်ရိုက် အလုပ်သမားခ စုစုပေါင်း",
        "m3": "၃။ တိုက်ရိုက် အသုံးစရိတ်များ",
        "royalty": "မူပိုင်ခွင့်ကြေး",
        "hire_plant": "စက်ပစ္စည်း ငှားရမ်းခ",
        "fuel_power_direct": "လောင်စာနှင့် လျှပ်စစ်",
        "direct_expenses_total": "တိုက်ရိုက် အသုံးစရိတ် စုစုပေါင်း",
        "prime_cost": "အခြေခံ ကုန်ကျစရိတ် (Prime Cost)",
        "m4": "၄။ စက်ရုံ အသုံးစရိတ်များ",
        "factory_rent": "စက်ရုံ ငှားရမ်းခ",
        "factory_rates": "စက်ရုံ အခွန်",
        "factory_insurance": "စက်ရုံ အာမခံ",
        "factory_power": "စက်ရုံ လျှပ်စစ်",
        "factory_salary": "စက်ရုံ ဝန်ထမ်းခ",
        "depreciation_plant": "စက်ပစ္စည်း တန်ဖိုးကျဆင်း",
        "repairs_plant": "စက်ပစ္စည်း ပြုပြင်ခ",
        "indirect_wages": "သွယ်ဝိုက် အလုပ်သမားခ",
        "factory_misc": "အထွေထွေ စက်ရုံစရိတ်",
        "factory_overhead_total": "စက်ရုံ အသုံးစရိတ် စုစုပေါင်း",
        "m5": "၅။ လုပ်ငန်း ဆောင်ရွက်ဆဲ (WIP)",
        "add_opening_wip": "အဖွင့် WIP",
        "less_closing_wip": "အပိတ် WIP",
        "production_cost": "ကုန်ထုတ်လုပ်မှု ကုန်ကျစရိတ် (Production Cost)",

        "trading_acc_title": "က။ အရောင်းအဝယ် စာရင်း (Trading Account)",
        "cash_sales": "အရောင်း",
        "credit_sales": "အကြွေး အရောင်း",
        "less_sales_return": "အရောင်းပြန်အမ်း နုတ်",
        "net_sales": "အရောင်း စုစုပေါင်း (Revenue)",
        "opening_stock_finished": "အဖွင့် ကုန်ချောလက်ကျန်",
        "add_purchases": "ကုန်ပစ္စည်း ဝယ်ယူမှု",
        "add_manufacturing_cost": "ကုန်ထုတ်လုပ်မှု ကုန်ကျစရိတ် ပေါင်း",
        "add_carriage_inward": "သယ်ယူပို့ဆောင်ခ",
        "add_duty": "အကောက်ခွန် ပေါင်း",
        "less_purchase_return": "ဝယ်ယူမှု ပြန်အမ်း နုတ်",
        "less_closing_stock": "အပိတ် ကုန်ချောလက်ကျန် နုတ်",
        "cogs_total": "COGS စုစုပေါင်း",
        "gross_profit": "အမြတ် (Gross Profit)",
        "pl_acc_title": "ခ။ အမြတ်အစွန်း စာရင်း (Profit & Loss Account)",
        "start_with_gp": "အမြတ် (Gross Profit) ဖြင့် စတင်",
        "other_income": "အခြား ဝင်ငွေများ",
        "other_income_total": "အခြား ဝင်ငွေ စုစုပေါင်း",
        "expenses": "စီမံခန့်ခွဲမှု အသုံးစရိတ်များ",
        "expenses_total": "အသုံးစရိတ် စုစုပေါင်း",
        "net_profit": "အသားတင် အမြတ် (Net Profit)",

        "bs_assets_title": "ပိုင်ဆိုင်မှုများ (ASSETS)",
        "bs_ca_title": "လက်ရှိ ပိုင်ဆိုင်မှုများ",
        "ca_inventories": "ကုန်ပစ္စည်းလက်ကျန်",
        "ca_receivable": "ရရန်ကျန်ငွေ",
        "ca_advance": "ကြိုတင်ပေးငွေ",
        "ca_cash": "လက်ထဲ/ဘဏ် ငွေသား",
        "current_assets_total": "လက်ရှိ ပိုင်ဆိုင်မှု စုစုပေါင်း",
        "bs_fa_title": "လက်ရှိမဟုတ်သော ပိုင်ဆိုင်မှုများ (Non Current Assets)",
        "nca_land": "မြေ",
        "nca_building": "အဆောက်အအုံ",
        "nca_machine": "စက်ပစ္စည်း",
        "nca_furniture": "ပရိဘောဂ",
        "nca_vehicle": "ယာဉ်",
        "less_depreciation": "တန်ဖိုးကျဆင်းမှု နုတ်",
        "fixed_assets_total": "ပုံသေ ပိုင်ဆိုင်မှု စုစုပေါင်း",
        "total_assets": "ပိုင်ဆိုင်မှု စုစုပေါင်း (TOTAL ASSETS)",
        "bs_liab_title": "အကြွေးများ (LIABILITIES)",
        "bs_cl_title": "လက်ရှိ အကြွေးများ",
        "liab_payable": "ပေးရန်ကျန်ငွေ",
        "liab_bank_loan": "ဘဏ် ချေးငွေ",
        "current_liabilities_total": "လက်ရှိ အကြွေး စုစုပေါင်း",
        "total_liabilities": "အကြွေး စုစုပေါင်း",
        "bs_cap_title": "အရင်းငွေ (CAPITAL)",
        "eq_capital": "အရင်း",
        "eq_retain": "စုဆောင်း အမြတ်",
        "eq_profit": "ယခုနှစ် အမြတ်",
        "eq_drawing": "ပိုင်ရှင် ထုတ်ယူမှု",
        "capital_total": "အရင်း စုစုပေါင်း",
        "liabilities_and_capital": "အကြွေးနှင့် အရင်း စုစုပေါင်း",
        "balanced_msg": "✓ ဟန်ချက်ညီပါသည် (Assets = Liabilities + Capital)",
        "not_balanced_msg": "✗ ကွာဟမှု: {} ကျပ်",

                # ... အပေါ်က ကုဒ်တွေ ...
        "cf_op_title": "က။ လုပ်ငန်း လည်ပတ်မှု လုပ်ဆောင်ချက်များမှ ငွေသား",
        "cf_net_profit": "အခွန်မဆိုင်မီ အသားတင် အမြတ်/အရှုံး",
        "cf_retain_earning": "စုဆောင်းအမြတ် တိုးလာမှု",
        "cf_amortization": "တန်ဖိုးလျော့ခြင်း (Amortization)",
        "cf_depreciation": "တန်ဖိုးကျဆင်းမှု (Depreciation)",
        "cf_op_profit": "လုပ်ငန်းလည်ပတ်မှု အမြတ် (Working Capital မဆိုင်မီ)",
        
        "cf_wc_title": "ခ။ လုပ်ငန်း လည်ပတ်မှု အရင်းအနှီး ပြောင်းလဲမှုများ",
        "cf_inv_change": "ကုန်ပစ္စည်းလက်ကျန် တိုး/ကျ",
        "cf_rec_change": "ရရန်ကျန်ငွေ တိုး/ကျ",
        "cf_pay_change": "ပေးရန်ကျန်ငွေ တိုး/ကျ",
        "cf_prep_change": "ကြိုတင်ပေးငွေ တိုး/ကျ",
        "cf_cash_from_op": "လုပ်ငန်းလည်ပတ်မှုမှ ရရှိသော ငွေသား",
        "cf_net_op": "လုပ်ငန်းလည်ပတ်မှုမှ ရရှိသော ငွေသား (Net)",
        
        "cf_inv_title": "ဂ။ ရင်းနှီးမြှုပ်နှံမှု လုပ်ဆောင်ချက်များမှ ငွေသား",
        "cf_invest_fa": "ပုံသေပိုင်ဆိုင်မှု ဝယ်ယူမှု",
        "cf_net_investing": "ရင်းနှီးမြှုပ်နှံမှုမှ ထွက်သွားသော ငွေသား (Net)",
        
        "cf_fin_title": "ဃ။ ငွေကြေးရှာဖွေမှု လုပ်ဆောင်ချက်များမှ ငွေသား",
        "cf_fin_draw": "ပိုင်ရှင် ထုတ်ယူမှု (Drawing)",
        "cf_net_financing": "ငွေကြေးရှာဖွေမှုမှ ထွက်သွားသော ငွေသား (Net)",
        
        "cf_summary_title": "ငွေသား အကျဉ်းချုပ်",
        "cf_net_change": "ငွေသား ပြောင်းလဲမှု (Net Change)",
        "cf_opening_cash": "ကာလအစ ငွေသား",
        "cf_closing_cash": "ကာလအဆုံး ငွေသား",
    },
    "en": {
        "period_end": "Period End",
        "as_at_date": "As at Date",
        "manufacturing_title": "Manufacturing Account",
        "trading_pl_title": "Trading and Profit & Loss Account",
        "balance_sheet_title": "Balance Sheet",
        "cash_flow_title": "Cash Flow Statement",

        "m1": "1. Direct Materials",
        "opening_stock_raw": "Opening Stock (Raw)",
        "purchases_raw": "Purchases (Raw)",
        "carriage_inward": "Carriage Inward",
        "customs_duty": "Customs Duty",
        "closing_stock_raw": "Closing Stock (Raw)",
        "cost_of_materials_used": "Cost of Materials Used",
        "m2": "2. Direct Labour",
        "wages_direct": "Direct Wages",
        "wages_overtime": "Overtime Wages",
        "wages_contract": "Contract Wages",
        "direct_labour_total": "Total Direct Labour",
        "m3": "3. Direct Expenses",
        "royalty": "Royalty",
        "hire_plant": "Hire of Plant",
        "fuel_power_direct": "Fuel & Power",
        "direct_expenses_total": "Total Direct Expenses",
        "prime_cost": "Prime Cost",
        "m4": "4. Factory Overhead",
        "factory_rent": "Factory Rent",
        "factory_rates": "Factory Rates",
        "factory_insurance": "Factory Insurance",
        "factory_power": "Factory Power",
        "factory_salary": "Factory Salary",
        "depreciation_plant": "Depreciation - Plant",
        "repairs_plant": "Repairs - Plant",
        "indirect_wages": "Indirect Wages",
        "factory_misc": "Misc Factory Exp",
        "factory_overhead_total": "Total Factory Overhead",
        "m5": "5. Work in Progress",
        "add_opening_wip": "Opening WIP",
        "less_closing_wip": "Closing WIP",
        "production_cost": "Production Cost",

        "trading_acc_title": "A. Trading Account",
        "cash_sales": "Sales",
        "credit_sales": "Credit Sales",
        "less_sales_return": "Less: Sales Returns",
        "net_sales": "Total Revenue",
        "opening_stock_finished": "Opening Stock (Finished)",
        "add_purchases": "Add: Purchases",
        "add_manufacturing_cost": "Add: Manufacturing Cost",
        "add_carriage_inward": "Add: Carriage Inward",
        "add_duty": "Add: Customs Duty",
        "less_purchase_return": "Less: Purchase Returns",
        "less_closing_stock": "Less: Closing Stock",
        "cogs_total": "Total COGS",
        "gross_profit": "Gross Profit",
        "pl_acc_title": "B. Profit & Loss Account",
        "start_with_gp": "Start with Gross Profit",
        "other_income": "Other Income",
        "other_income_total": "Total Other Income",
        "expenses": "Administrative Expenses",
        "expenses_total": "Total Expenses",
        "net_profit": "Net Profit",

        "bs_assets_title": "ASSETS",
        "bs_ca_title": "Current Assets",
        "ca_inventories": "Inventories",
        "ca_receivable": "A/C Receivable",
        "ca_advance": "Advance Payments",
        "ca_cash": "Cash",
        "current_assets_total": "Total Current Assets",
        "bs_fa_title": "Non Current Assets (Less: Depreciation)",
        "nca_land": "Land",
        "nca_building": "Building",
        "nca_machine": "Machine",
        "nca_furniture": "Furniture",
        "nca_vehicle": "Vehicle",
        "less_depreciation": "Less: Depreciation",
        "fixed_assets_total": "Total Non Current Assets",
        "total_assets": "TOTAL ASSETS",
        "bs_liab_title": "LIABILITIES",
        "bs_cl_title": "Current Liabilities",
        "liab_payable": "A/C Payable",
        "liab_bank_loan": "Bank Loan",
        "current_liabilities_total": "Total Current Liabilities",
        "total_liabilities": "TOTAL LIABILITIES",
        "bs_cap_title": "CAPITAL",
        "eq_capital": "Capital",
        "eq_retain": "Retain Earning",
        "eq_profit": "Profit for the year",
        "eq_drawing": "Drawing",
        "capital_total": "Total Capital",
        "liabilities_and_capital": "TOTAL LIABILITIES & CAPITAL",
        "balanced_msg": "✓ Balanced (Assets = Liabilities + Capital)",
        "not_balanced_msg": "✗ Difference: {} Kyats",

        "cf_op_title": "A. CASH FLOW FROM OPERATION ACTIVITIES",
        "cf_net_profit": "Net Profit before Taxation",
        "cf_retain_earning": "Increase in Retain Earning",
        "cf_amortization": "Amortization",
        "cf_depreciation": "Depreciation",
        "cf_op_profit": "Operation Profit before Working Capital",
        
        "cf_wc_title": "B. WORKING CAPITAL CHANGES",
        "cf_inv_change": "Changes in Inventories",
        "cf_rec_change": "Changes in A/C Receivable",
        "cf_pay_change": "Changes in Creditors",
        "cf_prep_change": "Changes in Prepayment",
        "cf_cash_from_op": "Cash used in / generated from operation",
        "cf_net_op": "Net cash inflow from Operation",
        
        "cf_inv_title": "C. CASH FLOW FROM INVESTING ACTIVITIES",
        "cf_invest_fa": "Purchase of Fixed Assets",
        "cf_net_investing": "Net Cash from Investing",
        
        "cf_fin_title": "D. CASH FLOW FROM FINANCING ACTIVITIES",
        "cf_fin_loan": "Increase in Loan",
        "cf_fin_draw": "Drawing",
        "cf_net_financing": "Net Cash from Financing",
        
        "cf_summary_title": "CASH SUMMARY",
        "cf_net_change": "Net Change in Cash",
        "cf_opening_cash": "Cash at Beginning",
        "cf_closing_cash": "Cash at End",
    }
}


def get_pdf_text(lang: str, key: str) -> str:
    return PDF_TRANSLATIONS.get(lang, PDF_TRANSLATIONS["my"]).get(key, key)

def format_date_ordinal(date_str: str) -> str:
    """ရက်စွဲကို 31st March 2024 ပုံစံဖြစ်အောင် ပြောင်းပေးတဲ့ Function"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        day = d.day
        if 11 <= day <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        return f"{day}{suffix} {d.strftime('%B %Y')}"
    except Exception:
        return date_str


# ============================================================
# 1. CALCULATION ENGINE
# ============================================================

def calculate_manufacturing(data: Dict[str, Any]) -> Dict[str, Any]:
    custom_data = data.get("custom_data", {})
    t = merge_template_with_data("manufacturing", data)

    dm = t["direct_materials"]["items"]
    cost_of_materials_used = (
        parse_number(dm["opening_stock_raw"]["value"])
        + parse_number(dm["purchases_raw"]["value"])
        + parse_number(dm["carriage_inward"]["value"])
        + parse_number(dm["customs_duty"]["value"])
        - parse_number(dm["closing_stock_raw"]["value"])
    )
    for item in custom_data.get("direct_materials", []):
        if item.get("value"):
            cost_of_materials_used += parse_number(item["value"])
    t["direct_materials"]["cost_of_materials_used"] = cost_of_materials_used

    dl = t["direct_labour"]["items"]
    direct_labour_total = (
        parse_number(dl["wages_direct"]["value"])
        + parse_number(dl["wages_overtime"]["value"])
        + parse_number(dl["wages_contract"]["value"])
    )
    for item in custom_data.get("direct_labour", []):
        if item.get("value"):
            direct_labour_total += parse_number(item["value"])
    t["direct_labour"]["direct_labour_total"] = direct_labour_total

    de = t["direct_expenses"]["items"]
    direct_expenses_total = (
        parse_number(de["royalty"]["value"])
        + parse_number(de["hire_plant"]["value"])
        + parse_number(de["fuel_power_direct"]["value"])
    )
    for item in custom_data.get("direct_expenses", []):
        if item.get("value"):
            direct_expenses_total += parse_number(item["value"])
    t["direct_expenses"]["direct_expenses_total"] = direct_expenses_total

    prime_cost = cost_of_materials_used + direct_labour_total + direct_expenses_total
    t["prime_cost"]["value"] = prime_cost

    fo = t["factory_overhead"]["items"]
    factory_overhead_total = sum(parse_number(item["value"]) for item in fo.values())
    for item in custom_data.get("factory_overhead", []):
        if item.get("value"):
            factory_overhead_total += parse_number(item["value"])
    t["factory_overhead"]["factory_overhead_total"] = factory_overhead_total

    wip = t["work_in_progress"]["items"]
    opening_wip = parse_number(wip["add_opening_wip"]["value"])
    closing_wip = parse_number(wip["less_closing_wip"]["value"])

    production_cost = prime_cost + factory_overhead_total + opening_wip - closing_wip
    t["production_cost"]["value"] = production_cost
    t["transfer_to_trading"]["value"] = production_cost
    
    t["custom_data"] = custom_data
    return t


def calculate_trading_pl(data: Dict[str, Any]) -> Dict[str, Any]:
    custom_data = data.get("custom_data", {})
    t = merge_template_with_data("trading_pl", data)

    sales = t["trading"]["sales"]["items"]
    net_sales = (
        parse_number(sales["cash_sales"]["value"])
        + parse_number(sales["credit_sales"]["value"])
        - parse_number(sales["less_sales_return"]["value"])
    )

    for item in custom_data.get("revenue", []):
        if item.get("value"):
            net_sales += parse_number(item["value"])
    
    if data.get("_total_revenue") is not None:
        net_sales = parse_number(data["_total_revenue"])
        
    t["trading"]["sales"]["net_sales"] = net_sales

    cogs = t["trading"]["cogs"]["items"]
    
    closing_stock = parse_number(cogs["less_closing_stock"]["value"])
    if data.get("closing_stock") is not None:
        closing_stock = parse_number(data["closing_stock"])
    elif data.get("closing_stock_finished") is not None:
        closing_stock = parse_number(data["closing_stock_finished"])
        
    cogs_total = (
        parse_number(cogs["opening_stock_finished"]["value"])
        + parse_number(cogs["add_purchases"]["value"])
        + parse_number(cogs["add_manufacturing_cost"]["value"])
        + parse_number(cogs["add_carriage_inward"]["value"])
        + parse_number(cogs["add_duty"]["value"])
        - parse_number(cogs["less_purchase_return"]["value"])
        - closing_stock
    )

    for item in custom_data.get("cos", []):
        if item.get("value"):
            cogs_total += parse_number(item["value"])
            
    if data.get("_total_cos") is not None:
        cogs_total = parse_number(data["_total_cos"])

    t["trading"]["cogs"]["cogs_total"] = cogs_total
    t["trading"]["cogs"]["items"]["less_closing_stock"]["value"] = closing_stock

    gross_profit = net_sales - cogs_total
    if data.get("_gross_profit") is not None:
        gross_profit = parse_number(data["_gross_profit"])
    t["trading"]["gross_profit"]["value"] = gross_profit

    oi = t["profit_loss"]["other_income"]["items"]
    other_income_total = sum(parse_number(item["value"]) for item in oi.values())
    t["profit_loss"]["other_income"]["other_income_total"] = other_income_total

    ex = t["profit_loss"]["expenses"]["items"]
    expenses_total = sum(parse_number(item["value"]) for item in ex.values())

    for item in custom_data.get("expenses", []):
        if item.get("value"):
            expenses_total += parse_number(item["value"])
            
    if data.get("_total_expenses") is not None:
        expenses_total = parse_number(data["_total_expenses"])

    t["profit_loss"]["expenses"]["expenses_total"] = expenses_total
    t["custom_data"] = custom_data

    net_profit = gross_profit + other_income_total - expenses_total
    if data.get("_net_profit") is not None:
        net_profit = parse_number(data["_net_profit"])
    t["profit_loss"]["net_profit"]["value"] = net_profit

    return t


def calculate_balance_sheet(data: Dict[str, Any]) -> Dict[str, Any]:
    t = merge_template_with_data("balance_sheet", data)

    ca = t["assets"]["current_assets"]["items"]
    current_assets_total = sum(parse_number(item["value"]) for item in ca.values())
    t["assets"]["current_assets"]["current_assets_total"] = current_assets_total

    fa = t["assets"]["fixed_assets"]["items"]
    fixed_assets_total = (
        sum(
            parse_number(v["value"])
            for k, v in fa.items()
            if not v.get("is_deduction", False)
        )
        - parse_number(fa["less_depreciation"]["value"])
    )
    t["assets"]["fixed_assets"]["fixed_assets_total"] = fixed_assets_total

    total_assets = current_assets_total + fixed_assets_total
    t["assets"]["total_assets"]["value"] = total_assets

    cl = t["liabilities"]["current_liabilities"]["items"]
    current_liabilities_total = sum(parse_number(item["value"]) for item in cl.values())
    t["liabilities"]["current_liabilities"]["current_liabilities_total"] = current_liabilities_total

    total_liabilities = current_liabilities_total
    t["liabilities"]["total_liabilities"]["value"] = total_liabilities

    cap = t["capital"]["items"]
    capital_total = (
        parse_number(cap["eq_capital"]["value"])
        + parse_number(cap["eq_retain"]["value"])
        + parse_number(cap["eq_profit"]["value"])
        - parse_number(cap["eq_drawing"]["value"])
    )
    t["capital"]["capital_total"] = capital_total

    liab_cap = total_liabilities + capital_total
    t["balance_check"]["liabilities_and_capital"]["value"] = liab_cap
    diff = total_assets - liab_cap
    t["balance_check"]["difference"] = diff
    t["balance_check"]["is_balanced"] = abs(diff) < 0.01
    return t


# ============================================================
# 2. HTML RENDER HELPERS
# ============================================================

def _build_html_header(client_name: str, title: str, period_str: str, business_name: str = "", business_type: str = "") -> str:
    # ၁။ ဖောက်သည်နာမည် (Client Name နဲ့ Business Name မတူမှ ပြမယ်)
    if client_name and client_name != business_name:
        name_html = f'<h1 style="color: #1f4788; margin: 0 0 10px 0; font-size: 18pt;">{client_name}</h1>'
    else:
        name_html = ""
    
    # ၂။ လုပ်ငန်းနာမည် + အမျိုးအစား
    business_info = ""
    if business_name and business_type:
        business_info = f"{business_name} ({business_type})"
    elif business_name:
        business_info = business_name
    elif business_type:
        business_info = f"({business_type})"
        
    b_info_html = f'<h2 style="color: #333; margin: 0 0 10px 0; font-size: 14pt;">{business_info}</h2>' if business_info else ""
    
    # ၃။ စာရင်းခေါင်းစဉ် + ကာလ (တစ်ကြောင်းတည်း ပေါင်းထားတယ်)
    title_period_html = f'<h3 style="font-size: 13pt; margin: 0; font-weight: bold; color: #1565c0;">{title} <span style="color: #666; font-weight: normal; font-size: 11pt;">- {period_str}</span></h3>'
    
    return f"""
    <div class="header" style="text-align: center; margin-bottom: 20px;">
        {name_html}
        {b_info_html}
        {title_period_html}
    </div>
    """

def _build_html_row(sr: str, label: str, value: float, is_subtotal=False, is_total=False,
                    is_deduction=False, is_bold=False):
    if is_subtotal:
        css_class = "subtotal-row"
    elif is_total:
        css_class = "total-row"
    else:
        css_class = ""

    amount_str = format_number(value, decimals=0)
    if is_deduction:
        amount_str = f"({amount_str})"

    label_style = "font-weight: bold;" if is_bold else ""

    return f"""
    <tr class="{css_class}">
        <td class="sr">{sr}</td>
        <td class="label" style="{label_style}">{label}</td>
        <td class="amount">{amount_str}</td>
    </tr>
    """


def _render_manufacturing_html(t: Dict[str, Any], lang: str) -> str:
    html = ""
    custom_data = t.get("custom_data", {})
    sr_counter = 1

    def get_sr():
        nonlocal sr_counter
        s = str(sr_counter)
        sr_counter += 1
        return s
    
    dm = t["direct_materials"]
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "m1")}</td></tr>'
    html += _build_html_row(get_sr(), get_pdf_text(lang, "opening_stock_raw"), dm["items"]["opening_stock_raw"]["value"])
    html += _build_html_row(get_sr(), get_pdf_text(lang, "purchases_raw"), dm["items"]["purchases_raw"]["value"])
    html += _build_html_row(get_sr(), get_pdf_text(lang, "carriage_inward"), dm["items"]["carriage_inward"]["value"])
    html += _build_html_row(get_sr(), get_pdf_text(lang, "customs_duty"), dm["items"]["customs_duty"]["value"])
    html += _build_html_row(get_sr(), get_pdf_text(lang, "closing_stock_raw"), dm["items"]["closing_stock_raw"]["value"], is_deduction=True)
    
    for item in custom_data.get("direct_materials", []):
        if item.get("label") and item.get("value", 0) > 0:
            html += _build_html_row(get_sr(), item["label"], item["value"])
            
    html += _build_html_row("", get_pdf_text(lang, "cost_of_materials_used"), dm["cost_of_materials_used"], is_subtotal=True)

    dl = t["direct_labour"]
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "m2")}</td></tr>'
    for k in ["wages_direct", "wages_overtime", "wages_contract"]:
        html += _build_html_row(get_sr(), get_pdf_text(lang, k), dl["items"][k]["value"])
        
    for item in custom_data.get("direct_labour", []):
        if item.get("label") and item.get("value", 0) > 0:
            html += _build_html_row(get_sr(), item["label"], item["value"])
            
    html += _build_html_row("", get_pdf_text(lang, "direct_labour_total"), dl["direct_labour_total"], is_subtotal=True)

    de = t["direct_expenses"]
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "m3")}</td></tr>'
    for k in ["royalty", "hire_plant", "fuel_power_direct"]:
        html += _build_html_row(get_sr(), get_pdf_text(lang, k), de["items"][k]["value"])
        
    for item in custom_data.get("direct_expenses", []):
        if item.get("label") and item.get("value", 0) > 0:
            html += _build_html_row(get_sr(), item["label"], item["value"])
            
    html += _build_html_row("", get_pdf_text(lang, "direct_expenses_total"), de["direct_expenses_total"], is_subtotal=True)

    html += _build_html_row("", get_pdf_text(lang, "prime_cost"), t["prime_cost"]["value"], is_total=True)

    fo = t["factory_overhead"]
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "m4")}</td></tr>'
    for k, item in fo["items"].items():
        html += _build_html_row(get_sr(), get_pdf_text(lang, k), item["value"])
        
    for item in custom_data.get("factory_overhead", []):
        if item.get("label") and item.get("value", 0) > 0:
            html += _build_html_row(get_sr(), item["label"], item["value"])
            
    html += _build_html_row("", get_pdf_text(lang, "factory_overhead_total"), fo["factory_overhead_total"], is_subtotal=True)

    wip = t["work_in_progress"]["items"]
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "m5")}</td></tr>'
    html += _build_html_row(get_sr(), get_pdf_text(lang, "add_opening_wip"), wip["add_opening_wip"]["value"])
    html += _build_html_row(get_sr(), get_pdf_text(lang, "less_closing_wip"), wip["less_closing_wip"]["value"], is_deduction=True)

    html += _build_html_row("", get_pdf_text(lang, "production_cost"), t["production_cost"]["value"], is_total=True)
    return html


def _render_trading_pl_html(t: Dict[str, Any], lang: str, data: Dict[str, Any]) -> str:
    html = ""
    sr_counter = 1

    def get_sr():
        nonlocal sr_counter
        s = str(sr_counter)
        sr_counter += 1
        return s

    def _build_row_5(sr, label, amt1="", amt2="", amt3="", css="", is_bold=False):
        label_style = "font-weight: bold;" if is_bold else ""
        return f"""
        <tr class="{css}">
            <td class="sr">{sr}</td>
            <td class="label" style="{label_style}">{label}</td>
            <td class="amount">{amt1}</td>
            <td class="amount">{amt2}</td>
            <td class="amount">{amt3}</td>
        </tr>
        """

    show_revenue = data.get("_show_revenue", {})
    show_cos = data.get("_show_cos", {})
    show_expenses = data.get("_show_expenses", {})
    show_other_income = data.get("_show_other_income", {})
    custom_data = t.get("custom_data", {})
    
    # --- 1. Revenue ---
    html += f'<tr class="section-header"><td colspan="5">{get_pdf_text(lang, "trading_acc_title")}</td></tr>'
    sales = t["trading"]["sales"]["items"]
    
    if show_revenue.get("cash_sales", True):
        html += _build_row_5(get_sr(), get_pdf_text(lang, "cash_sales"), "", format_number(sales["cash_sales"]["value"]), "")
    # if show_revenue.get("credit_sales", True):
        # html += _build_row_5(get_sr(), get_pdf_text(lang, "credit_sales"), "", format_number(sales["credit_sales"]["value"]), "")
    if show_revenue.get("sales_return", True):
        html += _build_row_5(get_sr(), get_pdf_text(lang, "less_sales_return"), "", f"({format_number(sales['less_sales_return']['value'])})", "")

    for item in custom_data.get("revenue", []):
        if item.get("label") and item.get("value", 0) > 0:
            html += _build_row_5(get_sr(), item["label"], "", format_number(item["value"]), "")

    # ⭐ အခြားဝင်ငွေများကို ဒီနေရာမှာ ထည့်မယ် (Amount 2 မှာ)
    html += f'<tr class="section-header"><td colspan="5">{get_pdf_text(lang, "other_income")}</td></tr>'
    oi = t["profit_loss"]["other_income"]["items"]
    for k, item in oi.items(): 
        if show_other_income.get(k, True):
            val = item.get("value", 0)
            if val > 0:
                html += _build_row_5(get_sr(), item["label_mm"] if lang=="my" else item["label_en"], "", format_number(val), "")
    html += _build_row_5("", get_pdf_text(lang, "other_income_total"), "", format_number(t["profit_loss"]["other_income"]["other_income_total"]), "", css="subtotal-row", is_bold=True)

    # ⭐ Net Sales (Revenue) ကို Amount 3 မှာ ပြမယ်
    revenue_label = "အရောင်း စုစုပေါင်း (Revenue)" if lang == "my" else "Total Revenue"
    html += _build_row_5("", revenue_label, "", "", format_number(t["trading"]["sales"]["net_sales"]), css="subtotal-row", is_bold=True)

    # --- 2. Cost of Production ---
    cogs = t["trading"]["cogs"]["items"]
    
    mfg_dm = parse_number(data.get("mfg_direct_material", 0))
    mfg_dl = parse_number(data.get("mfg_direct_labour", 0))
    mfg_oh = parse_number(data.get("mfg_direct_overhead", 0))
    
    cost_of_prod_rows = ""
    if mfg_dm > 0:
        cost_of_prod_rows += _build_row_5(get_sr(), "Direct Materials", "", format_number(mfg_dm), "")
    if mfg_dl > 0:
        cost_of_prod_rows += _build_row_5(get_sr(), "Direct Labour", "", format_number(mfg_dl), "")
    if mfg_oh > 0:
        cost_of_prod_rows += _build_row_5(get_sr(), "Direct Overhead", "", format_number(mfg_oh), "")
        
    prod_cost = mfg_dm + mfg_dl + mfg_oh

    if show_cos.get("opening_stock_finished", True):
        cost_of_prod_rows += _build_row_5(get_sr(), get_pdf_text(lang, "opening_stock_finished"), "", format_number(cogs["opening_stock_finished"]["value"]), "")
    if show_cos.get("purchases", True):
        cost_of_prod_rows += _build_row_5(get_sr(), get_pdf_text(lang, "add_purchases"), "", format_number(cogs["add_purchases"]["value"]), "")
    if show_cos.get("carriage_inward", True):
        cost_of_prod_rows += _build_row_5(get_sr(), get_pdf_text(lang, "add_carriage_inward"), "", format_number(cogs["add_carriage_inward"]["value"]), "")
    if show_cos.get("purchase_return", True):
        cost_of_prod_rows += _build_row_5(get_sr(), get_pdf_text(lang, "less_purchase_return"), "", f"({format_number(cogs['less_purchase_return']['value'])})", "")

    for item in custom_data.get("cos", []):
        if item.get("label") and item.get("value", 0) > 0:
            cost_of_prod_rows += _build_row_5(get_sr(), item["label"], "", format_number(item["value"]), "")

    total_cogs_before_closing = prod_cost + cogs["opening_stock_finished"]["value"] + cogs["add_purchases"]["value"] + cogs["add_carriage_inward"]["value"] - cogs["less_purchase_return"]["value"]
    for item in custom_data.get("cos", []):
        total_cogs_before_closing += item.get("value", 0)

    html += cost_of_prod_rows

    if show_cos.get("closing_stock_finished", True):
        html += _build_row_5(get_sr(), get_pdf_text(lang, "less_closing_stock"), "", f"({format_number(cogs['less_closing_stock']['value'])})", "")

    # ⭐ COGS ကို Amount 3 မှာ ပြမယ် (စာသားပြောင်းထားတယ်)
    cogs_label = "ကုန်ရောင်း တန်ဖိုး (Cost of Sales)" if lang == "my" else "Cost of Sales"
    html += _build_row_5("", cogs_label, "", "", format_number(t["trading"]["cogs"]["cogs_total"]), css="cogs-row", is_bold=True)

    gp = t["trading"]["gross_profit"]
    gp_label = get_pdf_text(lang, "gross_profit") if gp["value"] >= 0 else ("အရှုံး" if lang=="my" else "Gross Loss")
    html += _build_row_5("", gp_label, "", "", format_number(gp["value"]), css="total-row", is_bold=True)

    # --- 3. P&L Account ---
    html += f'<tr class="section-header"><td colspan="5">{get_pdf_text(lang, "pl_acc_title")}</td></tr>'

    html += f'<tr class="section-header"><td colspan="5">{get_pdf_text(lang, "expenses")}</td></tr>'
    
    # ⭐ ဘာသာစကားအလိုက် စာသားတွေ ပြောင်းမယ်
    if lang == "my":
        default_expenses_map = {
            "staff_salary": "ဝန်ထမ်းခနှင့် အလုပ်သမားခ",
            "tax_other": "အခွန်နှင့် အခြား",
            "electricity": "လျှပ်စစ်",
            "telephone": "တယ်လီဖုန်း",
            "fuel": "လောင်စာ",
            "repair_maintenance": "ပြုပြင်ထိန်းသိမ်းမှု",
            "general_expenses": "အထွေထွေ သုံးစွဲမှု",
        }
    else:
        default_expenses_map = {
            "staff_salary": "Staff Salary & Wages",
            "tax_other": "Tax & Other",
            "electricity": "Electricity",
            "telephone": "Telephone",
            "fuel": "Fuel",
            "repair_maintenance": "Repair & Maintenance",
            "general_expenses": "General Expenses",
        }

    for key, label in default_expenses_map.items():
        if show_expenses.get(key, True):
            val = parse_number(data.get(key, 0))
            if val > 0:
                # ⭐ ဒီနေရာမှာ Amount 2 ကော်လံထဲ ထည့်မယ်
                html += _build_row_5(get_sr(), label, "", format_number(val), "")
    
    for item in custom_data.get("expenses", []):
        if item.get("label") and item.get("value", 0) > 0:
            # ⭐ ဒီနေရာမှာလည်း Amount 2 ကော်လံထဲ ထည့်မယ်
            html += _build_row_5(get_sr(), item["label"], "", format_number(item["value"]), "")
    
    # ⭐ စုစုပေါင်း အသုံးစရိတ်ကို Amount 3 မှာ ထည့်မယ်
    html += _build_row_5("", get_pdf_text(lang, "expenses_total"), "", "", format_number(t["profit_loss"]["expenses"]["expenses_total"]), css="subtotal-row", is_bold=True)

    np_ = t["profit_loss"]["net_profit"]
    np_label = get_pdf_text(lang, "net_profit") if np_["value"] >= 0 else ("အသားတင် အရှုံး" if lang=="my" else "Net Loss")
    html += _build_row_5("", np_label, "", "", format_number(np_["value"]), css="total-row", is_bold=True)
    
    return html

def _render_balance_sheet_html(t: Dict[str, Any], lang: str, data: Dict[str, Any]) -> str:
    html = ""
    sr_counter = 1

    def get_sr():
        nonlocal sr_counter
        s = str(sr_counter)
        sr_counter += 1
        return s

    # Column ၂ ခု အတွက် Row ဆောက်တဲ့ Function
    def _build_row_4(sr, label, amt1="", amt2="", css="", is_bold=False):
        label_style = "font-weight: bold;" if is_bold else ""
        return f"""
        <tr class="{css}">
            <td class="sr">{sr}</td>
            <td class="label" style="{label_style}">{label}</td>
            <td class="amount">{amt1}</td>
            <td class="amount">{amt2}</td>
        </tr>
        """

    show_assets = data.get("_show_bs_assets", {})
    show_equity = data.get("_show_bs_equity", {})
    show_liab = data.get("_show_bs_liab", {})

    # ==================== ASSETS ====================
    html += f'<tr class="section-header"><td colspan="4">{get_pdf_text(lang, "bs_assets_title")}</td></tr>'

    # --- A. Non Current Assets ---
    total_nca_val = t["assets"]["fixed_assets"]["fixed_assets_total"]
    html += _build_row_4("", f"A. {get_pdf_text(lang, 'bs_fa_title')}", "", format_number(total_nca_val), is_bold=True)

    fa = t["assets"]["fixed_assets"]["items"]
    for k, item in fa.items():
        if show_assets.get(k, True):
            is_ded = item.get("is_deduction", False)
            val_str = format_number(item["value"])
            if is_ded:
                val_str = f"({val_str})"
            html += _build_row_4(get_sr(), get_pdf_text(lang, k), val_str, "")

    # --- B. Current Assets ---
    total_ca_val = t["assets"]["current_assets"]["current_assets_total"]
    html += _build_row_4("", f"B. {get_pdf_text(lang, 'bs_ca_title')}", "", format_number(total_ca_val), is_bold=True)

    ca = t["assets"]["current_assets"]["items"]
    for k, item in ca.items():
        if show_assets.get(k, True):
            html += _build_row_4(get_sr(), get_pdf_text(lang, k), format_number(item["value"]), "")

    # Total Assets
    html += _build_row_4("", get_pdf_text(lang, "total_assets"), "", format_number(t["assets"]["total_assets"]["value"]), css="total-row", is_bold=True)

    # ==================== CAPITAL AND LIABILITIES ====================
    # ⭐ ခေါင်းစဉ်ပြောင်းမယ်
    cap_liab_title = "CAPITAL AND LIABILITIES" if lang == "en" else "အရင်းနှင့် အကြွေးများ"
    html += f'<tr class="section-header"><td colspan="4">{cap_liab_title}</td></tr>'
    
    # --- C. Total Capital ---
    total_cap_val = t["capital"]["capital_total"]
    html += _build_row_4("", f"C. {get_pdf_text(lang, 'capital_total')}", "", format_number(total_cap_val), is_bold=True)
    
    cap = t["capital"]["items"]
    if show_equity.get("eq_capital", True):
        html += _build_row_4(get_sr(), get_pdf_text(lang, "eq_capital"), format_number(cap["eq_capital"]["value"]), "")
    if show_equity.get("eq_retain", True):
        html += _build_row_4(get_sr(), get_pdf_text(lang, "eq_retain"), format_number(cap["eq_retain"]["value"]), "")
    if show_equity.get("eq_profit", True):
        html += _build_row_4(get_sr(), get_pdf_text(lang, "eq_profit"), format_number(cap["eq_profit"]["value"]), "")
    if show_equity.get("eq_drawing", True):
        html += _build_row_4(get_sr(), get_pdf_text(lang, "eq_drawing"), f"({format_number(cap['eq_drawing']['value'])})", "")

    # --- D. Total Current Liabilities ---
    total_cl_val = t["liabilities"]["current_liabilities"]["current_liabilities_total"]
    html += _build_row_4("", f"D. {get_pdf_text(lang, 'current_liabilities_total')}", "", format_number(total_cl_val), is_bold=True)

    cl = t["liabilities"]["current_liabilities"]["items"]
    for k, item in cl.items():
        if show_liab.get(k, True):
            html += _build_row_4(get_sr(), get_pdf_text(lang, k), format_number(item["value"]), "")

    # ⭐ "Total Current Liabilities" အောက်က လိုင်းကို ဖျောက်ထားပါတယ်။

    html += _build_row_4("", get_pdf_text(lang, "total_liabilities"), "", format_number(t["liabilities"]["total_liabilities"]["value"]), css="total-row", is_bold=True)

    html += _build_row_4("", get_pdf_text(lang, "liabilities_and_capital"), "", format_number(t["balance_check"]["liabilities_and_capital"]["value"]), css="total-row", is_bold=True)

    # Balance Check
    diff = t["balance_check"]["difference"]
    is_balanced = t["balance_check"]["is_balanced"]
    if is_balanced:
        msg = get_pdf_text(lang, "balanced_msg")
        css_class = "balanced"
    else:
        msg = get_pdf_text(lang, "not_balanced_msg").format(format_number(diff, decimals=0))
        css_class = "not-balanced"

    html += f'<tr class="{css_class}"><td colspan="4" style="text-align:center; font-weight:bold; padding: 10px;">{msg}</td></tr>'
    return html

def _render_cash_flow_html(data: Dict[str, Any], lang: str) -> str:
    html = ""
    sr_counter = 1

    def get_sr():
        nonlocal sr_counter
        s = str(sr_counter)
        sr_counter += 1
        return s

    # --- A. OPERATING ACTIVITIES ---
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "cf_op_title")}</td></tr>'
    
    net_profit = parse_number(data.get("net_profit", 0))
    retain_change = parse_number(data.get("retain_earning_change", 0))
    amortization = parse_number(data.get("amortization", 0))
    dep = parse_number(data.get("depreciation", 0))
    
    html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_net_profit"), net_profit)
    html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_retain_earning"), retain_change)
    html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_amortization"), amortization)
    html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_depreciation"), dep)

    op_profit = net_profit + retain_change + amortization + dep
    html += _build_html_row("", get_pdf_text(lang, "cf_op_profit"), op_profit, is_subtotal=True)

    # --- B. WORKING CAPITAL CHANGES ---
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "cf_wc_title")}</td></tr>'
    
    inv_chg = parse_number(data.get("change_inventories", 0))
    rec_chg = parse_number(data.get("change_receivable", 0))
    pay_chg = parse_number(data.get("change_payable", 0))
    prep_chg = parse_number(data.get("change_prepayment", 0))
    
    if inv_chg != 0:
        html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_inv_change"), inv_chg, is_deduction=(inv_chg < 0))
    if rec_chg != 0:
        html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_rec_change"), rec_chg, is_deduction=(rec_chg < 0))
    if pay_chg != 0:
        html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_pay_change"), pay_chg, is_deduction=(pay_chg < 0))
    if prep_chg != 0:
        html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_prep_change"), prep_chg, is_deduction=(prep_chg < 0))

    total_wc_change = inv_chg + rec_chg + pay_chg + prep_chg
    html += _build_html_row("", get_pdf_text(lang, "cf_cash_from_op"), total_wc_change, is_subtotal=True, is_deduction=(total_wc_change < 0))
    
    net_op = op_profit + total_wc_change
    html += _build_html_row("", get_pdf_text(lang, "cf_net_op"), net_op, is_total=True, is_deduction=(net_op < 0))

    # --- C. INVESTING ACTIVITIES ---
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "cf_inv_title")}</td></tr>'
    invest_fa = parse_number(data.get("investing_purchase_fa", 0))
    if invest_fa != 0:
        html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_invest_fa"), invest_fa, is_deduction=(invest_fa < 0))
    
    net_investing = invest_fa
    html += _build_html_row("", get_pdf_text(lang, "cf_net_investing"), net_investing, is_total=True, is_deduction=(net_investing < 0))

    # --- D. FINANCING ACTIVITIES ---
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "cf_fin_title")}</td></tr>'
    fin_draw = parse_number(data.get("financing_drawing", 0))
    if fin_draw != 0:
        html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_fin_draw"), fin_draw, is_deduction=(fin_draw < 0))
    
    net_financing = fin_draw
    html += _build_html_row("", get_pdf_text(lang, "cf_net_financing"), net_financing, is_total=True, is_deduction=(net_financing < 0))

    # --- CASH SUMMARY ---
    html += f'<tr class="section-header"><td colspan="3">{get_pdf_text(lang, "cf_summary_title")}</td></tr>'
    
    net_chg = net_op + net_investing + net_financing
    open_cash = parse_number(data.get("opening_cash", 0))
    close_cash = open_cash + net_chg
    
    html += _build_html_row("", get_pdf_text(lang, "cf_net_change"), net_chg, is_subtotal=True, is_deduction=(net_chg < 0))
    html += _build_html_row(get_sr(), get_pdf_text(lang, "cf_opening_cash"), open_cash)
    html += _build_html_row("", get_pdf_text(lang, "cf_closing_cash"), close_cash, is_total=True)

    return html

# ============================================================
# 3. MAIN PUBLIC API
# ============================================================

def generate_pdf(
    statement_type: str,
    client_name: str,
    data: Dict[str, Any],
    period_end: str = "",
    as_at_date: str = "",
    output_path: Optional[str] = None,
    lang: str = "my",
    business_type: str = "", 
    business_name: str = "", 
    client_id: int = None,
) -> bytes:

    # ⭐⭐⭐ အရေးကြီးဆုံး အပိုင်း ⭐⭐⭐
    # client_id ပါလာရင် Database ကနေ လုပ်ငန်းနာမည်ကို အတင်း ဆွဲထုတ်မယ်
    if client_id:
        try:
            client_db = db.get_client(client_id)
            if client_db:
                business_name = client_db.get("business_name", "")
                if not client_name:
                    client_name = client_db.get("name", "")
                if not business_type:
                    business_type = client_db.get("business_type", "")
        except Exception:
            pass
    # =================================

    titles = {
        "manufacturing": get_pdf_text(lang, "manufacturing_title"),
        "trading_pl": get_pdf_text(lang, "trading_pl_title"),
        "balance_sheet": get_pdf_text(lang, "balance_sheet_title"),
        "cash_flow": get_pdf_text(lang, "cash_flow_title"),
    }

    if statement_type not in titles:
        raise ValueError(f"မသိသော statement type: {statement_type}")

    if statement_type == "manufacturing":
        data["period_end"] = period_end
        t_res = calculate_manufacturing(data)
        if lang == "en":
            period_str = f"For the year ended {format_date_ordinal(period_end)}"
        else:
            period_str = f"ကာလကုန်: {format_date_ordinal(period_end)}"
        table_html = _render_manufacturing_html(t_res, lang)
        
    elif statement_type == "trading_pl":
        data["period_end"] = period_end
        t_res = calculate_trading_pl(data)

        if data.get("_total_revenue") is not None:
            t_res["trading"]["sales"]["net_sales"] = data["_total_revenue"]
        if data.get("_total_cos") is not None:
            t_res["trading"]["cogs"]["cogs_total"] = data["_total_cos"]
        if data.get("_gross_profit") is not None:
            t_res["trading"]["gross_profit"]["value"] = data["_gross_profit"]
        if data.get("_total_expenses") is not None:
            t_res["profit_loss"]["expenses"]["expenses_total"] = data["_total_expenses"]
        if data.get("_net_profit") is not None:
            t_res["profit_loss"]["net_profit"]["value"] = data["_net_profit"]
        if lang == "en":
            period_str = f"For the year ended {format_date_ordinal(period_end)}"
        else:
            period_str = f"ကာလကုန်: {format_date_ordinal(period_end)}"
        table_html = _render_trading_pl_html(t_res, lang, data)

    elif statement_type == "balance_sheet":
        data["as_at_date"] = as_at_date
        t_res = calculate_balance_sheet(data)
        period_str = f"As at {format_date_ordinal(as_at_date)}" if lang == "en" else f"ရက်စွဲ: {format_date_ordinal(as_at_date)}"
        table_html = _render_balance_sheet_html(t_res, lang, data) 

    elif statement_type == "cash_flow":
        data["period_end"] = period_end
        if lang == "en":
            period_str = f"For the year ended {format_date_ordinal(period_end)}"
        else:
            period_str = f"ကာလကုန်: {format_date_ordinal(period_end)}"
        table_html = _render_cash_flow_html(data, lang)
    
    col_count = 5 if statement_type == "trading_pl" else 3
    th_amounts = ""
    if col_count == 5:
        th_amounts = """
            <th class="amount" style="width: 15%;">Amount (MMK)</th>
            <th class="amount" style="width: 15%;">Amount (MMK)</th>
            <th class="amount" style="width: 15%;">Amount (MMK)</th>
        """
    else:
        th_amounts = '<th class="amount" style="width: 20%;">Amount (MMK)</th>'

    # ⭐ Header ကို ဒီနေရာမှာ သေချာခေါ်ပါတယ်
    header_html = _build_html_header(client_name, titles[statement_type], period_str, business_name, business_type)
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @font-face {{
                font-family: 'Pyidaungsu';
                src: url('file://{FONT_REGULAR}');
                font-weight: normal;
            }}
            @font-face {{
                font-family: 'Pyidaungsu';
                src: url('file://{FONT_BOLD}');
                font-weight: bold;
            }}

            @page {{
                size: A4 portrait;
                margin: 15mm;
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-family: 'Pyidaungsu';
                    font-size: 8pt;
                    color: #777;
                }}
                @bottom-left {{
                    content: "Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}";
                    font-family: 'Pyidaungsu';
                    font-size: 8pt;
                    color: #777;
                }}
            }}

            body {{
                font-family: 'Pyidaungsu', sans-serif;
                font-size: 9pt;
                color: #212121;
            }}

            .header {{ text-align: center; margin-bottom: 15px; }}
            .header h1 {{ font-size: 16pt; font-weight: bold; color: #1f4788; margin: 0; }}
            .header h2 {{ font-size: 13pt; font-weight: bold; margin: 5px 0 0 0; }}
            .header .period {{ font-size: 10pt; color: #666; margin-top: 5px; }}
            .header .business-type {{ font-size: 10pt; color: #555; margin-top: 3px; font-weight: bold; }}

            hr {{ border: 1px solid #1f4788; margin-bottom: 10px; }}

            table {{ width: 100%; border-collapse: collapse; }}
            td {{ padding: 2px 6px; }}
            .sr {{ width: 5%; text-align: center; }}
            .label {{ text-align: left; }}
            .amount {{ text-align: right; }}

            .section-header td {{
                background-color: #e3f2fd; color: #1565c0; font-weight: bold;
                padding-top: 8px; padding-bottom: 4px;
                border-top: 1px solid #90caf9; border-bottom: 1px solid #90caf9;
            }}

            .sub-section td {{
                font-weight: bold; color: #333; padding-top: 6px; padding-bottom: 6px;
            }}

            .cogs-row td {{
                background-color: #f5f5f5; 
                color: #333; 
                font-weight: bold; 
                border-top: 1px solid #ddd;
            }}

            .subtotal-row td {{
                background-color: #f5f5f5; font-weight: bold; border-top: 1px solid #ddd;
            }}

            .total-row td {{
                background-color: #fff3e0; color: #e65100; font-weight: bold; font-size: 11pt;
                border-top: 2px solid #e65100; border-bottom: 2px solid #e65100;
            }}

            .balanced td {{ color: #2e7d32; background-color: #e8f5e9; }}
            .not-balanced td {{ color: #c62828; background-color: #ffebee; }}
        </style>
    </head>
    <body>
        {header_html}
        <hr>
        <table>
            <thead>
                <tr style="background-color: #f5f5f5; border-bottom: 2px solid #333;">
                    <th class="sr">Sr.</th>
                    <th class="label">Particular</th>
                    {th_amounts}
                </tr>
            </thead>
            <tbody>
                {table_html}
            </tbody>
        </table>
    </body>
    </html>
    """

    pdf_bytes = HTML(string=full_html).write_pdf()

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes