# Kidney Biopsy Report Generator

A web application for generating standardized kidney biopsy reports from shorthand notation, designed to streamline the report writing process for pathologists.

## Features

- **Shorthand to Report Conversion**: Enter shorthand codes and automatically generate full medical reports
- **Live Preview**: See the report generate in real-time as you type
- **Transplant Biopsy Support**: Full support for transplant kidney biopsies with Banff scoring
- **Copy to Clipboard**: One-click copy of formatted reports for LIMS integration
- **Standardized Phrases**: Over 150 pre-mapped medical phrases ensure consistency
- **Patient Information Management**: Easy entry of NHS numbers, hospital numbers, and patient details

## Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:3000`

### Docker Deployment

```bash
docker-compose up
```

## Example Shorthand

```
NHS: 234 4567 2345
HN: 31098674
NS: 25-67890
Name: Smith
Coder: CR
Consent: PISv.8
Date of biopsy: 12/07/2025
LM: CM, C2M1
Glom: 31, Gs7, Ss1_NOS, Mm1, Mc1, G2, Cg1
TI: ATI micro, IFTA20, CTCI1, T1, I1_I-IFTA3, TI2
Ves: A3, 2IL_1Ar, Cv2, Caa0, V0, Ah1, Ptc1
IHC: C4d0, SV40_0
EM: EM0
IFFR: FR_0
CONCLUSION: BL, MVI+, MildIFTA
COMMENT: MVI+, DP
```

## Shorthand Reference

### Light Microscopy (LM)
- **C**: Cortex only
- **M**: Medulla only
- **CM**: Cortex and medulla
- **C2M1**: 2 samples of cortex, 1 of medulla

### Glomeruli (Glom)
- **Number**: Total glomeruli count
- **GSx**: Globally sclerosed (x = count)
- **SSx_variant**: Segmental sclerosis
- **MM0-3**: Mesangial matrix grades
- **MC0-3**: Mesangial cellularity
- **G0-3**: Glomerulitis grades
- **CG0-3**: Capillary double contours

### Tubulointerstitium (TI)
- **ATI1/2/micro**: Acute tubular injury
- **IFTAxx**: Fibrosis percentage
- **T0-3**: Tubulitis grades
- **I_I-IFTA**: Inflammation scores
- **TI0-3**: Total inflammation

### Blood Vessels (Ves)
- **Ax**: Artery count
- **CV0-3**: Fibrointimal thickening
- **V0-3**: Endarteritis
- **AH0-3**: Arteriolar hyalinosis
- **PTC0-3**: Peritubular capillaritis

## Railway Deployment

1. Create a new project on Railway
2. Connect your GitHub repository
3. Add environment variables:
   - `PORT`: 8000 (for backend)
   - `NEXT_PUBLIC_API_URL`: Your backend URL
4. Deploy both services

## Development

### Project Structure

```
kidney-report-generator/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic
│   │   └── data/             # Phrase mappings
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js app directory
│   ├── components/           # React components
│   └── package.json
└── docker-compose.yml
```

### API Endpoints

- `POST /api/generate`: Generate report from shorthand
- `POST /api/validate`: Validate shorthand codes
- `GET /api/phrases/{report_type}`: Get available phrases
- `GET /health`: Health check

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is designed for clinical use in pathology departments.

## Support

For issues or questions, please open an issue on GitHub.