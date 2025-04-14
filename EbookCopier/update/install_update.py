import sys
import zipfile
import shutil
import time
import stat
import argparse
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def validate_zip_path(path_str):
    if not Path(path_str).exists:
        logger.debug(f"zip path does not exist: {path_str}")
        raise argparse.ArgumentTypeError(f"Path does not exist: {path_str}")

    if Path(path_str).suffix != ".zip":
        logger.debug(f"File type is not a zip file: {path_str}")
        raise argparse.ArgumentTypeError(f"Not a zip file: {path_str}")
    return Path(path_str)


def validate_restart_path(path_str):
    if not Path(path_str).exists:
        logger.debug(f"bat path does not exist: {path_str}")
        raise argparse.ArgumentTypeError(f"Path does not exist: {path_str}")
    if Path(path_str).suffix != ".bat":
        logger.debug(f"File type is not a bat file: {path_str}")
        raise argparse.ArgumentTypeError(f"Not a bat file: {path_str}")
    return Path(path_str)


def start_logger():
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "update.log"

    # Create logger for this script
    logger = logging.getLogger("update_script")
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler and logging level for file
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Console handler
    con = logging.StreamHandler()
    con.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    con.setFormatter(formatter)

    # add handlers to logger
    logger.addHandler(fh)
    logger.addHandler(con)

    logger.info(f"Logger initialized. Log File: {log_file}")
    return logger


def main():
    try:
        parser = argparse.ArgumentParser(
            description="Unzip EbookCopier Zip and merge with existing directory"
        )
        parser.add_argument(
            "-p", "--zip_path",
            type=validate_zip_path,
            required=True,
            help="Path to the zip file to extract and install"
        )
        parser.add_argument(
            "-r", "--restart_path",
            required=True,
            help="Path to restart bat, to restart main program"
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the zip file after successful extraction"
        )
        # Parse args, and set type
        args = parser.parse_args()
        args.zip_path = Path(args.zip_path)
        args.restart_path = Path(args.restart_path)
        logger.debug(f"zip path: {args.zip_path}, restart path: {args.restart_path}, delete zip: {args.delete}")
        # unzip and move the zip file
        if not unzip_and_merge(args.zip_path, delete_after=args.delete):
            logger.error("Failed to unzip and install update")
            return False

        if restart_main(args.restart_path):
            logger.info("Restarting main application")
            time.sleep(1)
            sys.exit(0)
        else:
            logger.info("Failed to restart main application")
            time.sleep(1)
            sys.exit(1)
    except Exception as e:
        logger.error(f"Update Failed, see log file for more informatiom {str(e)}")


def restart_main(bat_path):
    try:
        cwd_path = bat_path.parent
        bat_file = bat_path.name

        if not bat_path.exists:
            logger.error(f"Batch file not found at {bat_path}")
            return False

        # change to the root directory first, important for relative paths

        # start the batch file
        subprocess.Popen(
            [bat_file],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=cwd_path
        )
        logger.info("Main application restarted successfully")
        return True

    except Exception as e:
        logger.error(f"Error restarting application {str(e)}")
        return False


def handle_remove_error(func, path, exc_info):
    """Handle read-only files when removing directories using onexc style"""
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def delete_zip_file(zip_path: Path, max_retries=3, delay=1) -> bool:
    """Safely delete a zip file with retry logic"""
    for attempt in range(max_retries):
        try:
            if zip_path.exists():
                zip_path.chmod(stat.S_IWRITE)  # Ensure write permissions
                zip_path.unlink()  # Path's version of os.remove
                logger.debug(f"Successfully delete zip file: {zip_path}")
                return True
        except PermissionError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to delete zip file after {max_retries} attempts: {e}")
                return False
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Unexpected error deleting zip file: {e}")
            return False
    return False


def unzip_and_merge(zip_path: Path, delete_after=True) -> bool:
    """
    Unzips a file and merges the contents of the 'EbookCopier-main' folder
    with the existing directory where the zip file is located.
    """
    try:
        # Get the parent directory of the zip file
        zip_dir = zip_path.parent.resolve()

        # Temporary extraction directory
        temp_extract = zip_dir / '_temp_extract'

        # Remove any existing temp directory using onexc
        if temp_extract.exists():
            shutil.rmtree(temp_extract, onexc=handle_remove_error)

        # Extract the entire zip to a temporary directory
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract)

        # Path to the EbookCopier-main folder inside the extracted contents
        source_folder = temp_extract / 'EbookCopier-main'

        if not source_folder.exists():
            logger.error("EbookCopier-main folder not found in the zip file")
            shutil.rmtree(temp_extract, onexc=handle_remove_error)
            return False

        def move_with_retry(src: Path, dst: Path, max_retries=3, delay=1) -> bool:
            """Move files with retry logic for permission issues"""
            for attempt in range(max_retries):
                try:
                    if dst.exists():
                        if dst.is_dir():
                            shutil.rmtree(dst, onexc=handle_remove_error)
                        else:
                            dst.chmod(stat.S_IWRITE)
                            dst.unlink()
                    shutil.move(str(src), str(dst))  # shutil still needs strings
                    return True
                except PermissionError:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
            return False

        # Move all contents from EbookCopier-main to the zip directory
        for item in source_folder.iterdir():
            src = item
            dst = zip_dir / item.name

            try:
                # If it's a directory that exists in both places, merge contents
                if src.is_dir() and dst.exists():
                    for sub_item in src.iterdir():
                        sub_src = sub_item
                        sub_dst = dst / sub_item.name
                        move_with_retry(sub_src, sub_dst)
                else:
                    move_with_retry(src, dst)

            except Exception as e:
                logger.warning(f"Warning could not move {item.name}: {str(e)}")
                continue
        logger.info("Successfully merged contents from EbookCopier-main")

        # Clean up temporary directory with onexc
        shutil.rmtree(temp_extract, onexc=handle_remove_error)

        # Delete the zip file if requested
        if delete_after:
            return delete_zip_file(zip_path)

        return True

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if 'temp_extract' in locals() and temp_extract.exists():
            shutil.rmtree(temp_extract, onexc=handle_remove_error)
        return False


if __name__ == "__main__":
    logger = start_logger()
    logger.info("Preparing to install...")
    time.sleep(5)
    main()
