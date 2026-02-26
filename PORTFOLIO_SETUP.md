# Adding Your Photo and Resume to the Portfolio

## Step 1: Upload Your Files

Upload these files to `/workspaces/glitchgetaway/escape/static/images/`:

1. **Profile Photo**: Name it `profile-photo.jpg` (or `.png`)
   - Recommended size: 400x550px (3:4 aspect ratio)
   - Professional headshot or portrait

2. **Resume PDF**: Name it `Jahnavi_Patel_Resume.pdf`
   - Keep under 5MB for fast loading

## Step 2: Collect Static Files

After uploading, run this command to collect all static files:

```bash
python manage.py collectstatic --noinput
```

This copies your files to the `staticfiles` directory that Django serves in production.

## Step 3: Test Locally

Start the development server:

```bash
python manage.py runserver
```

Visit `http://localhost:8000/` to see your portfolio with the photo and resume.

## File Locations

- **Development**: `escape/static/images/`
- **Production**: Django automatically serves from `staticfiles/`

## Notes

- If you change the photo filename, update it in the template at line 271
- If you change the resume filename, update it in the template at lines 229 and 243
- Supported photo formats: `.jpg`, `.jpeg`, `.png`, `.webp`
