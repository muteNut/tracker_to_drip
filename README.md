# Migrate to Drip

Conversion script to migrate from SimpleInnovations [Period Tracker and Calendar](https://simpleinnovation.us/my-calendar-period-tracker) to [Drip](https://bloodyhealth.gitlab.io/).

Based on the provided [more_cycle_data](https://bloodyhealth.gitlab.io/assets/more-cycle-data.csv), the converter takes `cyclesData_device.json` and `dayEntries_device.json` to generate a CSV file to be imported into the Drip App.

## Prerequisites

* **Python 3.x** installed on your system.
* **Git** installed on your system (or just download the python script).

## Getting Started

Clone this repository to your local machine:
   ```bash
   git clone https://github.com/muteNut/tracker_to_drip.git
   ```
**or**
download the [script](converter.py) directly and put it into a newly created directory, e.g. `tracker_to_drip`.

## Data Preparation
Before running the script, you need to export your raw data from the SimpleInnovations app.

1. Open the SimpleInnovations Period Tracker app and navigate to the backup/export settings.
2. Export your data to your device.
3. Locate the exported files, specifically making sure you have `cyclesData_device.json` and `dayEntries_device.json`.
4. Move or copy these two JSON files into the root folder of this project (e.g. `tracker_to_drip`).

## Execution

Run the converter script directly from terminal. Navigate to the root folder first, then execute it:

```bash
cd tracker_to_drip
python converter.py --entries="dayEntries_device.json" --cycles="cyclesData_device.json" --out="export.csv"
```

> **Note:** If your source files have different names, simply update the `--entries` and `--cycles` arguments accordingly. The script will generate an `export.csv` file upon successful completion.

## Importing into Drip

Once the script has finished running:

1. Transfer the newly generated `export.csv` file to your mobile device.
2. Open the **Drip** app.
3. Navigate to **Settings** > **Import/Export**.
4. Select the import option, locate your `export.csv` file, and load your data into the app.
