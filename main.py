import json
import time
import sys
import os
import glob
from pathlib import Path
from datetime import datetime

# Import colorama for colored terminal output
try:
    from colorama import Fore, Back, Style, init

    # Initialize colorama
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: colorama not installed. Install with: pip install colorama")
    print("   Running in plain text mode...\n")
    COLORAMA_AVAILABLE = False


    # Create dummy color classes
    class DummyColor:
        def __getattr__(self, name):
            return ""


    Fore = Back = Style = DummyColor()

from modules.LeMistral_client import lemistral_rescue_me, set_csv, get_csv
from modules.cleaner import lemistral_helper_action
from modules.kody_art import show_cody


class DataCleanerREPL:
    def __init__(self):
        self.csv_path = None
        self.strategies_json = None
        self.df = None
        self.final_data = None

        # Detect project root directory automatically
        self.project_root = self._detect_project_root()
        self.data_dir = os.path.join(self.project_root, "data")
        self.outputs_dir = os.path.join(self.project_root, "outputs")

        # Ensure directories exist
        self._ensure_directories()

    def _detect_project_root(self):
        """Detects the project root directory automatically"""
        # Start from the current file's directory
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)

        # Look for common project indicators
        indicators = [
            'requirements.txt',
            'setup.py',
            'pyproject.toml',
            '.git',
            'modules',  # Our specific module directory
            'README.md',
            'main.py',
        ]

        # Search up to 5 levels up
        search_dir = current_dir
        for _ in range(5):
            for indicator in indicators:
                if os.path.exists(os.path.join(search_dir, indicator)):
                    return search_dir

            parent = os.path.dirname(search_dir)
            if parent == search_dir:  # Reached filesystem root
                break
            search_dir = parent

        # Fallback to current directory
        return current_dir

    def _ensure_directories(self):
        """Ensures data and outputs directories exist"""
        for directory in [self.data_dir, self.outputs_dir]:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    print(f"{Fore.YELLOW}📁 Created directory: {Fore.WHITE}{directory}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}✗ Error creating directory {directory}: {e}{Style.RESET_ALL}")

    def show_banner(self):
        """Displays the startup banner with colors"""
        show_cody()
        time.sleep(2)

        print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 70)
        print(Fore.CYAN + Style.BRIGHT + "  🧹✨ INTERACTIVE DATA CLEANER - REPL ✨🧹")
        print(Fore.CYAN + Style.BRIGHT + "=" * 70 + Style.RESET_ALL)

        print(f"\n{Fore.YELLOW}📂 Project root:    {Fore.WHITE}{self.project_root}")
        print(f"{Fore.YELLOW}📁 Data directory:  {Fore.WHITE}{self.data_dir}")
        print(f"{Fore.YELLOW}💾 Output directory: {Fore.GREEN}{self.outputs_dir}{Style.RESET_ALL}\n")

    def show_menu(self):
        """Displays the main menu with colors"""
        print("\n" + Fore.MAGENTA + Style.BRIGHT + "─" * 70)
        print(Fore.MAGENTA + Style.BRIGHT + "📋 MAIN MENU")
        print(Fore.MAGENTA + Style.BRIGHT + "─" * 70 + Style.RESET_ALL)

        print(f"{Fore.GREEN}1. {Fore.WHITE}📂 Load CSV file")
        print(f"{Fore.GREEN}2. {Fore.WHITE}🔍 Analyze data and generate cleaning strategies")
        print(f"{Fore.GREEN}3. {Fore.WHITE}📋 View cleaning strategies")
        print(f"{Fore.GREEN}4. {Fore.WHITE}🧹 Apply data cleaning")
        print(f"{Fore.GREEN}5. {Fore.WHITE}📊 View clean data summary")
        print(f"{Fore.GREEN}6. {Fore.WHITE}⚖️  View original vs clean data")
        print(f"{Fore.GREEN}7. {Fore.WHITE}💾 Export clean data")
        print(f"{Fore.GREEN}8. {Fore.WHITE}🔄 Reset process")
        print(f"{Fore.GREEN}9. {Fore.WHITE}❓ Help")
        print(f"{Fore.RED}0. {Fore.WHITE}👋 Exit")

        print(Fore.MAGENTA + Style.BRIGHT + "─" * 70 + Style.RESET_ALL)

    def find_csv_files(self):
        """Searches for CSV files in the data/ directory"""
        csv_files = []

        # Search in data/ directory
        if os.path.exists(self.data_dir):
            csv_files.extend(glob.glob(os.path.join(self.data_dir, "*.csv")))

        # Search in data/ subdirectories
        if os.path.exists(self.data_dir):
            csv_files.extend(glob.glob(os.path.join(self.data_dir, "**", "*.csv"), recursive=True))

        # Remove duplicates and sort
        csv_files = sorted(list(set(csv_files)))

        return csv_files

    def load_csv(self):
        """Loads a CSV file with automatic detection and number selection"""
        if self.csv_path:
            print(f"\n{Fore.YELLOW}⚠️  A file is already loaded: {Fore.CYAN}{self.csv_path}{Style.RESET_ALL}")
            overwrite = input(f"{Fore.YELLOW}Do you want to load a new one? (y/n): {Style.RESET_ALL}").strip().lower()
            if overwrite != 'y':
                return

        # Search for CSV files
        csv_files = self.find_csv_files()

        if not csv_files:
            print(f"\n{Fore.YELLOW}⚠️  No CSV files found in '{self.data_dir}' directory{Style.RESET_ALL}")
            manual = input(
                f"{Fore.CYAN}Do you want to enter the path manually? (y/n): {Style.RESET_ALL}").strip().lower()
            if manual == 'y':
                path = input(f"\n{Fore.CYAN}Enter the CSV file path: {Style.RESET_ALL}").strip()
                self._load_csv_path(path)
            return

        # Display found files
        print(f"\n{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📂 CSV files found in '{self.data_dir}':")
        print(f"{Fore.CYAN}   Total: {Fore.YELLOW}{len(csv_files)}{Fore.CYAN} file(s){Style.RESET_ALL}\n")

        for i, csv_file in enumerate(csv_files, 1):
            # Display file information
            file_size = os.path.getsize(csv_file) / 1024  # KB
            relative_path = os.path.relpath(csv_file, self.project_root)
            print(f"{Fore.GREEN}{i}. {Fore.WHITE}{relative_path} {Fore.YELLOW}({file_size:.1f} KB){Style.RESET_ALL}")

        print(f"\n{Fore.BLUE}{len(csv_files) + 1}. {Fore.WHITE}✏️  Enter path manually{Style.RESET_ALL}")
        print(f"{Fore.RED}0. {Fore.WHITE}❌ Cancel{Style.RESET_ALL}")

        # Select file
        while True:
            try:
                choice = input(f"\n{Fore.CYAN}Select a file (number): {Style.RESET_ALL}").strip()

                if choice == '0':
                    print(f"{Fore.RED}✗ Operation cancelled{Style.RESET_ALL}")
                    return

                choice_num = int(choice)

                # Manual option
                if choice_num == len(csv_files) + 1:
                    path = input(f"\n{Fore.CYAN}Enter the CSV file path: {Style.RESET_ALL}").strip()
                    self._load_csv_path(path)
                    return

                # File selection
                if 1 <= choice_num <= len(csv_files):
                    path = csv_files[choice_num - 1]
                    self._load_csv_path(path)
                    return
                else:
                    print(f"{Fore.RED}✗ Number out of range (1-{len(csv_files) + 1}). Try again.{Style.RESET_ALL}")

            except ValueError:
                print(f"{Fore.RED}✗ Invalid input. Enter a number.{Style.RESET_ALL}")

    def _load_csv_path(self, path):
        """Loads a CSV file given its path"""
        try:
            set_csv(path)
            self.csv_path = path
            # Reset previous data
            self.strategies_json = None
            self.df = None
            self.final_data = None

            relative_path = os.path.relpath(path, self.project_root)
            print(f"{Fore.GREEN}✓ File loaded successfully: {Fore.CYAN}{relative_path}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Error loading file: {e}{Style.RESET_ALL}")

    def analyze_data(self):
        """Analyzes data and generates strategies"""
        if not self.csv_path:
            print(f"\n{Fore.RED}✗ You must first load a CSV file (option 1){Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔍 Analyzing data and generating cleaning strategies...{Style.RESET_ALL}")

        relative_path = os.path.relpath(self.csv_path, self.project_root)
        print(f"{Fore.YELLOW}    File: {Fore.WHITE}{relative_path}{Style.RESET_ALL}")

        try:
            self.strategies_json, self.df = lemistral_rescue_me()
            print(
                f"\n{Fore.GREEN}✓ Analysis completed. Found {Fore.YELLOW}{len(self.strategies_json)}{Fore.GREEN} problem(s).{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Error analyzing data: {e}{Style.RESET_ALL}")

    def show_strategies(self):
        """Displays cleaning strategies"""
        if not self.strategies_json:
            print(f"\n{Fore.RED}✗ You must first analyze the data (option 2){Style.RESET_ALL}")
            return

        print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 70)
        print(Fore.CYAN + Style.BRIGHT + "🔍 DETECTED CLEANING STRATEGIES")
        print(Fore.CYAN + Style.BRIGHT + "=" * 70 + Style.RESET_ALL)

        for i, strategy in enumerate(self.strategies_json, 1):
            print(
                f"\n{Fore.YELLOW}[{i}] {Fore.CYAN}Column: {Fore.WHITE}{Style.BRIGHT}{strategy['column']}{Style.RESET_ALL}")
            print(f"    {Fore.MAGENTA}Problem:  {Fore.WHITE}{strategy['problem']}{Style.RESET_ALL}")
            print(f"    {Fore.GREEN}Strategy: {Fore.WHITE}{strategy['strategy']}{Style.RESET_ALL}")
            print(f"    {Fore.BLUE}Reason:   {Fore.WHITE}{strategy['reason']}{Style.RESET_ALL}")
            print(f"    {Fore.CYAN}{'─' * 66}{Style.RESET_ALL}")

    def apply_cleaning(self):
        """Applies cleaning strategies"""
        if not self.strategies_json or self.df is None:
            print(f"\n{Fore.RED}✗ You must first analyze the data (option 2){Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🧹 Applying cleaning strategies...{Style.RESET_ALL}")

        try:
            self.final_data = lemistral_helper_action(self.strategies_json, self.df)
            print(f"{Fore.GREEN}✓ Cleaning applied successfully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Error applying cleaning: {e}{Style.RESET_ALL}")

    def show_summary(self):
        """Displays a summary of clean data"""
        if self.final_data is None:
            print(f"\n{Fore.RED}✗ You must first apply cleaning (option 4){Style.RESET_ALL}")
            return

        print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 70)
        print(Fore.CYAN + Style.BRIGHT + "📊 CLEAN DATA SUMMARY")
        print(Fore.CYAN + Style.BRIGHT + "=" * 70 + Style.RESET_ALL)

        print(
            f"\n{Fore.YELLOW}Dimensions: {Fore.GREEN}{self.final_data.shape[0]}{Fore.WHITE} rows × {Fore.GREEN}{self.final_data.shape[1]}{Fore.WHITE} columns{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}First 10 rows:{Style.RESET_ALL}")
        print(self.final_data.head(10))

        print(f"\n{Fore.CYAN}DataFrame Info:{Style.RESET_ALL}")
        print(self.final_data.info())

        print(f"\n{Fore.CYAN}Descriptive Statistics:{Style.RESET_ALL}")
        print(self.final_data.describe())

    def compare_data(self):
        """Compares original vs clean data"""
        if self.df is None or self.final_data is None:
            print(f"\n{Fore.RED}✗ You must first analyze (option 2) and apply cleaning (option 4){Style.RESET_ALL}")
            return

        print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 70)
        print(Fore.CYAN + Style.BRIGHT + "⚖️  COMPARISON: ORIGINAL VS CLEAN DATA")
        print(Fore.CYAN + Style.BRIGHT + "=" * 70 + Style.RESET_ALL)

        # Original data
        print(f"\n{Fore.RED}📊 ORIGINAL DATA:{Style.RESET_ALL}")
        print(
            f"   {Fore.YELLOW}Dimensions: {Fore.WHITE}{self.df.shape[0]} rows × {self.df.shape[1]} columns{Style.RESET_ALL}")
        print(f"   {Fore.YELLOW}Null values per column:{Style.RESET_ALL}")

        null_counts = self.df.isnull().sum()
        has_nulls = False
        for col, count in null_counts.items():
            if count > 0:
                has_nulls = True
                print(f"      {Fore.RED}{col}: {count}{Style.RESET_ALL}")

        if not has_nulls:
            print(f"      {Fore.GREEN}None!{Style.RESET_ALL}")

        # Clean data
        print(f"\n{Fore.GREEN}✨ CLEAN DATA:{Style.RESET_ALL}")
        print(
            f"   {Fore.YELLOW}Dimensions: {Fore.WHITE}{self.final_data.shape[0]} rows × {self.final_data.shape[1]} columns{Style.RESET_ALL}")
        print(f"   {Fore.YELLOW}Null values per column:{Style.RESET_ALL}")

        null_counts_clean = self.final_data.isnull().sum()
        has_nulls_clean = False
        for col, count in null_counts_clean.items():
            if count > 0:
                has_nulls_clean = True
                print(f"      {Fore.RED}{col}: {count}{Style.RESET_ALL}")

        if not has_nulls_clean:
            print(f"      {Fore.GREEN}None! 🎉{Style.RESET_ALL}")

        # Statistics
        rows_removed = self.df.shape[0] - self.final_data.shape[0]
        percentage = (self.final_data.shape[0] / self.df.shape[0] * 100) if self.df.shape[0] > 0 else 0

        print(f"\n{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
        print(f"{Fore.RED}📉 Rows removed:  {Fore.WHITE}{rows_removed}{Style.RESET_ALL}")
        print(
            f"{Fore.GREEN}📈 Rows retained: {Fore.WHITE}{self.final_data.shape[0]} ({percentage:.2f}%){Style.RESET_ALL}")

    def export_data(self):
        """Exports clean data to the outputs directory"""
        if self.final_data is None:
            print(f"\n{Fore.RED}✗ You must first apply cleaning (option 4){Style.RESET_ALL}")
            return

        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate suggested name based on original file
        if self.csv_path:
            original_name = os.path.basename(self.csv_path)
            name_without_ext = os.path.splitext(original_name)[0]
            suggested_name = f"{name_without_ext}_clean_{timestamp}.csv"
        else:
            suggested_name = f"clean_data_{timestamp}.csv"

        # Default path in outputs directory
        default_path = os.path.join(self.outputs_dir, suggested_name)

        print(f"\n{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}💾 Export clean data{Style.RESET_ALL}")
        print(
            f"{Fore.YELLOW}   Suggested path: {Fore.GREEN}{os.path.relpath(default_path, self.project_root)}{Style.RESET_ALL}")

        path = input(f"\n{Fore.CYAN}Press Enter to use suggested path or enter another path: {Style.RESET_ALL}").strip()
        if not path:
            path = default_path

        # Create directory if it doesn't exist
        output_dir = os.path.dirname(path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(f"{Fore.GREEN}✓ Directory created: {output_dir}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}✗ Error creating directory: {e}{Style.RESET_ALL}")
                return

        try:
            self.final_data.to_csv(path, index=False)
            file_size = os.path.getsize(path) / 1024  # KB
            relative_path = os.path.relpath(path, self.project_root)

            print(f"\n{Fore.GREEN}{'═' * 70}")
            print(f"✓ DATA EXPORTED SUCCESSFULLY!")
            print(f"{'═' * 70}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📁 Location: {Fore.WHITE}{relative_path}{Style.RESET_ALL}")
            print(
                f"{Fore.CYAN}📊 Dimensions: {Fore.WHITE}{self.final_data.shape[0]} rows × {self.final_data.shape[1]} columns{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💾 Size: {Fore.WHITE}{file_size:.1f} KB{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}✗ Error exporting: {e}{Style.RESET_ALL}")

    def reset(self):
        """Resets the process"""
        print(f"\n{Fore.YELLOW}⚠️  WARNING: This will reset the current session{Style.RESET_ALL}")
        confirm = input(
            f"{Fore.YELLOW}Are you sure you want to reset? Current data will be lost (y/n): {Style.RESET_ALL}").strip().lower()

        if confirm == 'y':
            self.csv_path = None
            self.strategies_json = None
            self.df = None
            self.final_data = None
            print(f"{Fore.GREEN}✓ Process reset successfully{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}Reset cancelled{Style.RESET_ALL}")

    def show_help(self):
        """Displays help"""
        print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 70)
        print(Fore.CYAN + Style.BRIGHT + "❓ HELP - RECOMMENDED WORKFLOW")
        print(Fore.CYAN + Style.BRIGHT + "=" * 70 + Style.RESET_ALL)

        print(f"""
{Fore.GREEN}1. Load CSV file (option 1){Style.RESET_ALL}
   {Fore.WHITE}• System automatically detects CSV files in 'data/' directory
   • Select file by entering its number
   • You can also enter a path manually{Style.RESET_ALL}

{Fore.GREEN}2. Analyze data (option 2){Style.RESET_ALL}
   {Fore.WHITE}• System will automatically detect problems
   • Generate cleaning strategies using AI{Style.RESET_ALL}

{Fore.GREEN}3. View strategies (option 3){Style.RESET_ALL}
   {Fore.WHITE}• Review proposed strategies before applying them
   • Understand what changes will be made{Style.RESET_ALL}

{Fore.GREEN}4. Apply cleaning (option 4){Style.RESET_ALL}
   {Fore.WHITE}• Execute strategies on your data
   • Creates cleaned version of the dataset{Style.RESET_ALL}

{Fore.GREEN}5. View summary (option 5){Style.RESET_ALL}
   {Fore.WHITE}• Inspect clean data statistics
   • See first rows and data types{Style.RESET_ALL}

{Fore.GREEN}6. View comparison (option 6){Style.RESET_ALL}
   {Fore.WHITE}• Compare original vs clean data side-by-side
   • See cleaning statistics and improvements{Style.RESET_ALL}

{Fore.GREEN}7. Export (option 7){Style.RESET_ALL}
   {Fore.WHITE}• Save clean data to 'outputs/' directory
   • Automatically adds timestamp to filename
   • Preserves original file in 'data/' directory{Style.RESET_ALL}

{Fore.GREEN}8. Reset (option 8){Style.RESET_ALL}
   {Fore.WHITE}• Start over with a different file
   • Clears current session data{Style.RESET_ALL}

{Fore.YELLOW}{'─' * 70}{Style.RESET_ALL}
{Fore.CYAN}COMPLETE WORKFLOW:{Style.RESET_ALL}
  {Fore.WHITE}1 → 2 → 3 → 4 → 5 or 6 → 7{Style.RESET_ALL}

{Fore.CYAN}EXAMPLE:{Style.RESET_ALL}
  {Fore.YELLOW}Input:  {Fore.WHITE}data/dirty_cafe_sales.csv{Style.RESET_ALL}
  {Fore.GREEN}Output: {Fore.WHITE}outputs/dirty_cafe_sales_clean_20260210_143022.csv{Style.RESET_ALL}

{Fore.CYAN}DIRECTORY STRUCTURE:{Style.RESET_ALL}
  {Fore.WHITE}project_root/
  ├── data/           {Fore.YELLOW}← Place your CSV files here{Style.RESET_ALL}
  └── outputs/        {Fore.GREEN}← Clean files are saved here{Style.RESET_ALL}
        """)

    def run(self):
        """Runs the REPL"""
        self.show_banner()

        # Display available CSV files at startup
        csv_files = self.find_csv_files()
        if csv_files:
            print(
                f"{Fore.GREEN}✓ Found {Fore.YELLOW}{len(csv_files)}{Fore.GREEN} CSV file(s) in '{self.data_dir}/'{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  No CSV files found in '{self.data_dir}/'{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   You can still load files manually (option 1){Style.RESET_ALL}")

        while True:
            self.show_menu()
            choice = input(f"\n{Fore.CYAN}Select an option: {Style.RESET_ALL}").strip()

            if choice == '1':
                self.load_csv()
            elif choice == '2':
                self.analyze_data()
            elif choice == '3':
                self.show_strategies()
            elif choice == '4':
                self.apply_cleaning()
            elif choice == '5':
                self.show_summary()
            elif choice == '6':
                self.compare_data()
            elif choice == '7':
                self.export_data()
            elif choice == '8':
                self.reset()
            elif choice == '9':
                self.show_help()
            elif choice == '0':
                print(f"\n{Fore.CYAN}{'═' * 70}")
                print(f"{Fore.GREEN}👋 Thanks for using Data Cleaner! See you later!")
                print(f"{Fore.CYAN}{'═' * 70}{Style.RESET_ALL}\n")
                sys.exit(0)
            else:
                print(f"\n{Fore.RED}✗ Invalid option. Please try again.{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")


if __name__ == "__main__":
    repl = DataCleanerREPL()
    repl.run()