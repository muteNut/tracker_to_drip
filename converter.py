import json
import csv
import argparse
from datetime import datetime, timedelta

def get_date_range(start_date, end_date):
    """Yields all dates between a start and end date (inclusive)."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def convert_drip_data(entries_file, cycles_file, output_file):
    # 1. Read the JSON files
    try:
        with open(entries_file, 'r', encoding='utf-8') as f:
            entries_json = json.load(f)
            entries_data = entries_json.get("entryList", []) if isinstance(entries_json, dict) else entries_json
            
        with open(cycles_file, 'r', encoding='utf-8') as f:
            cycles_json = json.load(f)
            cycles_data = cycles_json.get("cycleList", []) if isinstance(cycles_json, dict) else cycles_json
    except Exception as e:
        print(f"Error reading input files: {e}")
        return

    # Define the exact Drip CSV columns
    columns = [
        "date", "temperature.value", "temperature.exclude", "temperature.time", "temperature.note", 
        "bleeding.value", "bleeding.exclude", "mucus.feeling", "mucus.texture", "mucus.value", "mucus.exclude", 
        "cervix.opening", "cervix.firmness", "cervix.position", "cervix.exclude", "note.value", "desire.value", 
        "sex.solo", "sex.partner", "sex.condom", "sex.pill", "sex.iud", "sex.patch", "sex.ring", "sex.implant", 
        "sex.diaphragm", "sex.none", "sex.other", "sex.note", "pain.cramps", "pain.ovulationPain", "pain.headache", 
        "pain.backache", "pain.nausea", "pain.tenderBreasts", "pain.migraine", "pain.other", "pain.note", 
        "mood.happy", "mood.sad", "mood.stressed", "mood.balanced", "mood.fine", "mood.anxious", "mood.energetic", 
        "mood.fatigue", "mood.angry", "mood.other", "mood.note"
    ]

    # 2. Build a master dictionary to merge dates
    master_data = {}

    # Map period days from cyclesData
    for cycle in cycles_data:
        if 'cycleStartDate' not in cycle or 'cycleEndDate' not in cycle:
            continue
            
        start = datetime.strptime(str(cycle['cycleStartDate']), '%Y%m%d')
        end = datetime.strptime(str(cycle['cycleEndDate']), '%Y%m%d')
        
        for single_date in get_date_range(start, end):
            date_str = single_date.strftime("%Y-%m-%d")
            if date_str not in master_data:
                master_data[date_str] = {}
            # Flag this specific date as a period day
            master_data[date_str]['is_period_day'] = True

    # Map daily entries from dayEntries
    for entry in entries_data:
        if "entrydatekey" not in entry:
            continue
            
        date_str = datetime.strptime(str(entry["entrydatekey"]), "%Y%m%d").strftime("%Y-%m-%d")
        if date_str not in master_data:
            master_data[date_str] = {}
            
        master_data[date_str]['entry'] = entry

    output_rows = []

    # 3. Process the merged data chronologically
    for date_str in sorted(master_data.keys()):
        data_for_day = master_data[date_str]
        entry = data_for_day.get('entry', {})
        is_period_day = data_for_day.get('is_period_day', False)
        
        row = {col: "" for col in columns}
        row["date"] = date_str
        
        compiled_notes = []
        if "note" in entry:
            compiled_notes.append(entry["note"])
        if "medicine" in entry:
            compiled_notes.append(f"Medicine: {entry['medicine']}")
            
        symptoms = entry.get("symptoms", "").split(",") if "symptoms" in entry else []
        moods = entry.get("moods", "").split(",") if "moods" in entry else []
        
        # --- Bleeding / Flow Logic ---
        # Drip formats: 0 = spotting, 1 = light, 2 = medium, 3 = heavy
        if "spotting" in symptoms:
            row["bleeding.value"] = "0"
            row["bleeding.exclude"] = "false"
            symptoms.remove("spotting")
        elif "flow" in entry:
            flow_val = entry["flow"]
            # Map old app's 1-4 scale to Drip's 1-3 scale
            mapped_flow = flow_val if flow_val <= 3 else 3
            row["bleeding.value"] = str(mapped_flow)
            row["bleeding.exclude"] = "false"
        elif is_period_day or "pStartedToday" in entry or "pEndedToday" in entry or "bleeding" in symptoms:
            # If the cycle file says it's a period day, but flow wasn't logged, default to light bleeding (1)
            row["bleeding.value"] = "1" 
            row["bleeding.exclude"] = "false"
            if "bleeding" in symptoms: symptoms.remove("bleeding")

        # --- Sex ---
        if entry.get("hadIntercorse") == 1 or entry.get("hadIntercourseProtected") == 1:
            row["sex.partner"] = "true"
        if entry.get("hadIntercourseProtected") == 1:
            row["sex.condom"] = "true"

        # --- Pain Mapping ---
        for s in list(symptoms):
            matched = False
            if s in ["cramps", "acramps", "baches"]:
                row["pain.cramps"] = "true"
                matched = True
            elif s == "headaches":
                row["pain.headache"] = "true"
                matched = True
            elif s == "backaches":
                row["pain.backache"] = "true"
                matched = True
            elif s in ["bsensitivity", "btenderness"]:
                row["pain.tenderBreasts"] = "true"
                matched = True
            if matched:
                symptoms.remove(s)

        # --- Moods & Energy Mapping ---
        if "fatigue" in symptoms:
            row["mood.fatigue"] = "true"
            symptoms.remove("fatigue")
            
        for m in list(moods):
            matched = False
            if m == "happy":
                row["mood.happy"] = "true"
                matched = True
            elif m == "sad":
                row["mood.sad"] = "true"
                matched = True
            elif m == "stressed":
                row["mood.stressed"] = "true"
                matched = True
            elif m == "anxious":
                row["mood.anxious"] = "true"
                matched = True
            elif m in ["exhausted", "sleepy"]:
                row["mood.fatigue"] = "true"
                matched = True
            elif m in ["cranky", "irritability", "frustrated"]:
                row["mood.angry"] = "true"
                matched = True
            if matched:
                moods.remove(m)

        # --- Catch-all Notes ---
        if symptoms:
            compiled_notes.append(f"Symptoms: {', '.join(symptoms)}")
        if moods:
            compiled_notes.append(f"Moods: {', '.join(moods)}")
            
        if compiled_notes:
            row["note.value"] = " | ".join(compiled_notes)
            
        output_rows.append(row)

    # 4. Write to target CSV
    try:
        with open(output_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(output_rows)
        print(f"Success! Converted {len(output_rows)} entries and saved to '{output_file}'")
    except Exception as e:
        print(f"Error writing to output file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge and convert JSON tracking data to Drip CSV format.")
    
    parser.add_argument("--entries", dest="entries_file", required=True, help="Path to dayEntries JSON")
    parser.add_argument("--cycles", dest="cycles_file", required=True, help="Path to cyclesData JSON")
    parser.add_argument("--out", dest="output_file", required=True, help="Path to output CSV")
    
    args = parser.parse_args()
    
    output_filename = args.output_file
    if not output_filename.lower().endswith('.csv'):
        print("Note: Output must be a CSV. Adjusting extension...")
        output_filename = output_filename.rsplit('.', 1)[0] + '.csv'

    convert_drip_data(args.entries_file, args.cycles_file, output_filename)
