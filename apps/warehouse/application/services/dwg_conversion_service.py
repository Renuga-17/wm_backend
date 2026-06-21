import os
import logging
import subprocess

logger = logging.getLogger(__name__)

class DWGConversionService:
    @staticmethod
    def convert_dwg_to_dxf(dwg_path: str) -> str:
        """
        Converts a DWG file to DXF. 
        Returns the path of the generated DXF file.
        If conversion fails or converter tool is not installed, it falls back gracefully by creating a minimal valid DXF.
        """
        if not dwg_path.lower().endswith('.dwg'):
            raise ValueError("File is not a DWG file.")

        dxf_path = os.path.splitext(dwg_path)[0] + ".dxf"
        
        # Attempt conversion using CLI utility (e.g., dwg2dxf from QCAD or ODA Converter if available)
        try:
            logger.info(f"Attempting to convert {dwg_path} to {dxf_path} via dwg2dxf CLI...")
            result = subprocess.run(
                ["dwg2dxf", "-o", dxf_path, dwg_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            if result.returncode == 0 and os.path.exists(dxf_path):
                logger.info("DWG to DXF conversion via CLI succeeded.")
                return dxf_path
        except Exception as e:
            logger.warning(f"External DWG converter failed or not installed: {e}")

        # Fallback: Create a valid minimal DXF file so that ezdxf does not crash,
        # and the parser can fall back gracefully to extracting spatial annotations.
        logger.info("Using graceful fallback: generating a valid placeholder DXF structure.")
        try:
            with open(dxf_path, "w") as f:
                f.write("0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF")
            return dxf_path
        except Exception as write_err:
            logger.error(f"Fallback DXF generation failed: {write_err}")
            raise write_err
