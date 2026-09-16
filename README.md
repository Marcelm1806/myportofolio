# Marcel Mikula — Personal Portfolio

A responsive personal portfolio developed for Platform-Based Programming at the Faculty of Computer Science, Universitas Indonesia.

The project started as a static About Me page. Tutorial 2 introduced database-backed experience entries; Assignment 2 added a project overview, individual project pages, and reusable page templates. Tutorial 3 adds project creation, title search, JSON/XML data delivery, and deletion with confirmation.

[Assignment 1 specification](https://pbp.cs.ui.ac.id/en/assignments/individual/tugas-1.html) · [Assignment 2 specification](https://pbp.cs.ui.ac.id/en/assignments/individual/tugas-2.html)

## Student Information

- **Name:** Marcel Mikula
- **NPM:** 2606816592
- **Class:** PBP A

## Current Features

- Profile, education, and Data & AI topics on the home page
- Database-backed project overview featuring Porsche, ING, and my bachelor's thesis
- Individual project pages with a return link to the overview
- Database-backed B. Braun experience with responsibilities, role progression, and employment period
- Shared navigation, footer, stylesheet, and skip link through `base.html`
- Responsive layouts, keyboard focus indicators, and reduced-motion support
- Native expandable project contributions using `<details>` and `<summary>`
- Empty states for the project and experience lists
- A 404 response for a project ID that does not exist
- Versioned fixtures for loading three projects and one experience entry
- A model-based project form with validation, CSRF protection, and success messages
- Project title search and JSON/XML endpoints with the same filter
- A native popover for confirming deletion through a CSRF-protected POST
- Twenty-eight automated tests covering the existing portfolio and the new form/data-delivery behavior

The frontend uses HTML5, CSS3, and Django Template Language. It uses CSS Grid, Flexbox, CSS variables, and `clamp()`; no frontend framework or JavaScript library is required.

## Pages and Navigation

| Page or section | URL | Content |
| --- | --- | --- |
| Home | `/` | Profile, education, and Data & AI |
| Projects | `/projects/` | All project records from the database |
| Title search | `/projects/?title=macan` | Case-insensitive matching on project titles |
| Add project | `/projects/add/` | GET displays the form; a valid POST creates a record |
| Projects as JSON | `/api/projects/` | Serialized project records; supports `?title=...` |
| Projects as XML | `/api/projects/xml/` | The same records and filter represented as XML |
| Delete project | `/projects/<uuid>/delete/` | POST only; linked through the confirmation popover |
| Project detail | `/projects/<uuid>/` | One selected project |
| Experience | `/experience/` | Professional experience from the database |
| Education | `/#education` | Education section on the home page |
| Skills | `/#skills` | Data & AI section on the home page |

The navigation uses named Django URLs. Education and Skills link to home-page sections, including when accessed from another page.

## Technologies and Development Environment

The recorded local test environment uses **Python 3.13.9**, **Django 6.1**, and **SQLite** on macOS. Dependencies are listed in `requirements.txt`, including WhiteNoise and python-dotenv. That file currently leaves dependency versions unpinned, so a later installation may resolve different versions.

## Project Structure

| Path | Responsibility |
| --- | --- |
| `portofolio/settings.py` | Project configuration, database selection, templates, and static files |
| `portofolio/urls.py` | Project-level routing, including the `main` application's URLs |
| `main/models.py` | The `Experience` and `Project` models |
| `main/forms.py` | `ProjectForm`, using the existing Project fields |
| `main/views.py` | Profile context and views for the home, experience, project list, and project detail pages |
| `main/urls.py` | Named routes in the `main` namespace |
| `main/tests.py` | Automated model, page, and fixture tests |
| `main/tests_tutorial3.py` | Creation, deletion, CSRF, filtering, JSON, and XML tests |
| `main/migrations/` | Versioned database schema changes |
| `main/fixtures/main/projects.json` | Three portfolio project records |
| `main/fixtures/main/experience.json` | The B. Braun experience record |
| `templates/base.html` | Shared document structure, navigation, footer, and content block |
| `templates/index.html` | Profile, education, and Data & AI content |
| `templates/projects.html` | Project list and empty state |
| `templates/projects_form.html` | Project creation form, help text, and validation errors |
| `templates/components/project_delete_modal.html` | Reusable deletion confirmation popover |
| `templates/project_detail.html` | Individual project content |
| `templates/experience.html` | Experience list and empty state |
| `static/css/style.css` | Shared styling and responsive rules |
| `static/css/tutorial3.css` | Form, search, message, and confirmation styles using the existing design tokens |
| `static/img/Download.jpeg` | Profile photograph |
| `manage.py` | Django management commands |

## Local Setup

These instructions are for a fresh checkout of the Tutorial 3 branch. Install Python 3.13 and Git first.

1. Clone the branch and enter the repository:

   ```bash
   git clone --branch feature/tutorial_3_forms https://github.com/Marcelm1806/myportofolio.git
   cd myportofolio
   ```

   To reproduce a particular submission, check out its submitted commit before continuing.

2. Create and activate a virtual environment.

   On macOS or Linux:

   ```bash
   python3.13 -m venv env
   source env/bin/activate
   ```

   On Windows PowerShell:

   ```powershell
   py -3.13 -m venv env
   .\env\Scripts\Activate.ps1
   ```

3. Install dependencies using the activated environment:

   ```bash
   python -m pip install -r requirements.txt
   ```

   Local development uses SQLite when `PRODUCTION` is unset or `False`. If you already have a local `.env` file or shell setting for production, set `PRODUCTION=False` for this setup. A fresh local checkout does not require PostgreSQL credentials.

4. Apply the committed migrations and load the portfolio data:

   ```bash
   python manage.py migrate
   python manage.py loaddata main/projects.json
   python manage.py loaddata main/experience.json
   ```

   On an empty database, the fixture commands install three projects and one experience record. Without loading them, the corresponding pages display their empty states.

5. Check the configuration and run the tests:

   ```bash
   python manage.py check
   python manage.py test
   ```

6. Start the development server:

   ```bash
   python manage.py runserver
   ```

   Open [the local portfolio](http://127.0.0.1:8000/). Stop the server with `Ctrl + C`.

## Portfolio Data and Design Decisions

### Models

`Project` stores short labels in `CharField` fields and longer summaries, contributions, and technology lists in `TextField` fields. A `BooleanField` marks featured work; a `PositiveIntegerField` controls display order. Each project has a UUID primary key used in its detail URL.

The model's default ordering places featured projects first, then uses `display_order` and `title`. The `technology_list` property splits the stored technology text into trimmed, non-empty lines for display as tags.

`Experience` stores the role title, organization, category, role timeline, responsibilities, and dates. Its `responsibility_list` property converts description lines into list items. An absent end date produces the ongoing status.

Employment dates in the B. Braun fixture are known to month precision. Their day component is normalized to 1, and the page displays only month and year. `started_at` uses `default=timezone.now`, allowing an explicit historical start date to be supplied when creating a record. [Django field reference](https://docs.djangoproject.com/en/6.1/ref/models/fields/#django.db.models.DateField.auto_now_add)

### Loading and Updating Data

The JSON fixtures are a reproducible source for the initial portfolio records. Views retrieve the imported records through the ORM; templates render those database values.

Fixture entries have fixed UUIDs. Loading the same fixture again updates those entries instead of creating additional copies. It also restores their fields to the fixture values, overwriting edits to those same records. Separately created records with different IDs are preserved. [Django fixture documentation](https://docs.djangoproject.com/en/6.1/howto/initial-data/)

To update the versioned portfolio content, edit the relevant fixture and reload it. The local SQLite database, virtual environment, and environment files are excluded from Git; migrations and fixtures are the files needed to rebuild the schema and initial portfolio data.

### Current Scope

Projects and experience are rendered from database records. Profile values are supplied by the view, while education and skills remain in the home template. Projects can be created and deleted through the browser, searched by title, and inspected as JSON or XML. Updating an existing project through a form is a possible future extension; fixtures and the Django shell remain available for content maintenance.

Authentication and ownership checks are not implemented at this tutorial stage. Anyone who can reach the application can use its create/delete forms. CSRF checks protect against cross-site request forgery; they do not decide who is allowed to manage a portfolio. Public deployment with editing enabled needs an authorization design in a later iteration.

## Testing and Verification

The Assignment 2 baseline completed **14 tests successfully** on my Mac. Tutorial 3 adds **14 tests**, giving **28 tests** in the current code. The new suite must be run locally before submission; the previous 14-test result does not verify the new implementation.

| Test group | Count | Coverage |
| --- | --- | --- |
| Tutorial 2 tests | 6 | Home and experience pages, navigation, missing page, model behavior, empty experience list, and completed status |
| Project list tests | 3 | Project content and template, empty state, and links from existing pages |
| Project detail tests | 3 | Selected project content, missing project ID, and detail links from the list |
| Project fixture test | 1 | Loading twice without duplicates while preserving an independently created project |
| Experience history test | 1 | Saving and displaying historical dates, organization, timeline, and responsibilities |
| Tutorial 3 write tests | 9 | Creation, invalid input, redirect behavior, preservation of other records, CSRF, deletion, missing IDs, and HTTP methods |
| Tutorial 3 data-delivery tests | 5 | JSON structure and ordering, shared title filtering, distinct empty states, XML content, and read-only endpoints |

Run the full suite and development checks with:

```bash
python manage.py test
python manage.py makemigrations --check --dry-run
git diff --check
```

The recorded Assignment 2 results were 14 passing tests, `No changes detected`, and no whitespace errors. That local test run also printed a warning about the missing collected `staticfiles/` directory; the test suite completed successfully. The full Tutorial 3 test suite completed successfully: 28 tests passed. This update adds no model fields or migrations.

Tests run against a separate test database. Example names used in test cases are test data. These checks exercise model behavior and rendered HTTP responses; they do not measure browser layout or verify the truth of portfolio claims.

For a manual browser check:

- Open the home, Projects, and Experience pages and follow each project detail link.
- Expand and collapse the contribution sections, and follow the return link from a detail page.
- Check desktop and narrow mobile widths, including approximately 390 pixels, for readable content and horizontal overflow.
- Use the keyboard to follow navigation and the skip link.
- Confirm that the three projects and the B. Braun responsibilities match the intended content.
- Add a temporary project, search for its title, inspect the filtered JSON/XML, cancel deletion once, and then delete only that temporary record.
- Check that invalid form input shows errors and retains the entered values. Refresh after a successful submission and confirm that it does not create another record.

## Weekly Progress

| Stage | Progress |
| --- | --- |
| Tutorial 0 | Created the repository, configured Git, prepared the virtual environment, and initialized Django. |
| Tutorial 1 | Built the About Me page with profile information, a photograph, and external links. |
| Assignment 1 | Added static projects, experience, education, and skills; implemented responsive styling and native interactive details. |
| Tutorial 2 | Introduced the `main` app, the `Experience` model, ORM-backed views, named URLs, migrations, and six tests. |
| Assignment 2 | Added the `Project` model and migration, project list and detail pages, shared templates, fixtures, and additional tests. Restored the B. Braun content as database records and extended experience fields. |
| Tutorial 3 | Added a Project ModelForm, title search, JSON/XML endpoints, the tutorial's JSON-to-template flow, POST-only deletion with confirmation, success messages, and 14 additional tests. |

## Reflective Questions

The Assignment 1 and Assignment 2 answers below describe their respective submitted versions. Tutorial 3 subsequently changed the project-list data flow as explained below; it does not change those historical submissions.

### Assignment 1

1. **Use of semantic HTML5**

   I used semantic HTML5 elements throughout the portfolio. The main content is divided into individual `<section>` elements for the profile, projects, experience, education, and skills. Each project and education entry uses an `<article>` because it represents an independent piece of content. I also used `<header>`, `<nav>`, `<main>`, and `<footer>` to describe the overall document structure. A description list (`<dl>`) represents labelled profile information, while unordered lists are used for technology tags and responsibilities. Finally, `<details>` and `<summary>` provide interactive project information without requiring JavaScript.

   These elements made the hierarchy of the page easier to understand and reduced the need for generic `<div>` elements. They also made the structure more accessible to screen readers and allowed related CSS rules to be organized into reusable components such as project cards, education cards, and section headings.

2. **Responsive-layout challenges**

   The main challenge was translating a wide desktop layout into a narrow mobile layout without making the content difficult to read. On desktop, the profile uses a two-column grid, the Porsche project spans the full project grid, and the ING and bachelor's-thesis cards appear next to each other. This arrangement could not fit naturally on a mobile screen.

   I therefore used media queries to change the profile grid into a single-column layout and reposition the identity, photograph, and biography in a logical reading order. Project and education grids also change to one column. Metadata, headings, tags, buttons, and company information are allowed to wrap when necessary. I prioritized the name, project titles, and written content while limiting the photograph's width and using `clamp()` for scalable typography. I tested the result by resizing the desktop browser and by using Brave's device emulator with an iPhone 12 Pro viewport of 390 × 844 pixels. I also checked that the page had no horizontal overflow and that all interactive elements remained usable.

3. **Limitations of the static website**

   Because the website is static, every project, experience entry, or text correction must currently be added directly to the HTML file. The page cannot retrieve portfolio entries from a database, provide project filters, process a contact form, or allow content to be updated through an administration interface. The project cards can reveal additional information using native HTML, but their data remains hard-coded.

   In the next iteration, I would most like to use Django's MVT architecture to create models for projects, experience, and education. The page could then render its content dynamically from a database, while an administration interface would make updates possible without editing the template. Additional functionality could include filtering projects by topic, a validated contact form, and individual project-detail pages. I would keep the current responsive and accessible HTML structure as the presentation layer for those dynamic features.

### Assignment 2

1. **What happens when a user opens the new portfolio page?**

   When the browser requests `/projects/`, Django receives the HTTP request and resolves its path. The project URL configuration, `portofolio/urls.py`, includes the application's routes. In `main/urls.py`, the `projects/` pattern selects `show_projects`; its name, `main:show_projects`, also lets templates generate this link with the `{% url %}` tag.

   The view prepares a context containing my name and `project_list = Project.objects.all()`. This is a QuerySet: the database is read when the template iterates over it. The `Project` model defines the stored fields and the ordering of the results.

   `render()` combines the context with `projects.html`. That template extends `base.html`, so the result includes the shared navigation and footer. Its loop renders one card per project, while the `{% empty %}` branch supplies a message when there are no records. Django returns the resulting HTML to the browser, which applies the stylesheet.

   For a detail page, the URL supplies a project's UUID to `show_project_detail`. The view looks up that record with `get_object_or_404()` and renders `project_detail.html`. A missing record produces a 404 response. [Django shortcuts](https://docs.djangoproject.com/en/6.1/topics/http/shortcuts/)

2. **Why store the section's data in a model?**

   A model separates portfolio content from presentation. My project list and detail page read the same `Project` record, so a change to its title or contribution can appear in both places. Adding another project does not require duplicating card markup: the template loop handles the new record.

   Field types express how values are used. Long descriptions belong in text fields, featured status is a boolean, and display order is a non-negative integer. Keeping these responsibilities in the model makes the templates easier to maintain and leaves room for later features such as forms, an administration interface, or filtering.

   This separation also improves testing: tests can create known records, request a page, and check its response. I can test an empty database independently of the portfolio data used during normal development. The fixtures make the initial content reproducible, while the database supplies the records displayed at runtime.

   There are still deliberate limits to this iteration. Education and skills remain static, and the portfolio does not yet provide an editing interface. The same MVT approach can be extended to those areas when needed.

3. **What is the difference between `makemigrations` and `migrate`?**

   `makemigrations` compares the model definitions with the state represented by existing migration files and writes a new migration describing the changes. `migrate` applies outstanding migrations to the selected database. Creating the migration file alone does not update that database. [Django migrations](https://docs.djangoproject.com/en/6.1/topics/migrations/)

   In this project, adding `Project` generated `0002_project.py`. Later, adding `organization` and `role_timeline` to `Experience`, extending its category choices, and changing the start-date default generated `0003_experience_organization_experience_role_timeline_and_more.py`. I applied those changes with:

   ```bash
   python manage.py makemigrations main
   python manage.py migrate
   ```

   The migration files belong in Git alongside the model changes. A fresh checkout can apply them with `migrate`. Portfolio records are imported separately through `loaddata`.

## Tutorial 3: Forms and Data Delivery

The implementation adapts [Tutorial 3](https://pbp.cs.ui.ac.id/en/tutorial/tutorial-3.html) to the existing portfolio. `ProjectForm` uses `organization`, `summary`, `contribution`, `technologies`, and the other existing fields. It does not introduce the tutorial example's differently named fields. `base.html` already supplies the document structure and the single `<main>` element; child templates fill its `content` block and use the existing `title` block.

On GET, `create_project` displays an unbound form. On POST, it binds the submitted data, validates it, saves one new record if valid, and redirects to the project list. Invalid input renders the same bound form with errors and the submitted values. An explicit method check binds even an empty POST so required-field errors are shown. [Django ModelForm documentation](https://docs.djangoproject.com/en/6.1/topics/forms/modelforms/)

`get_projects_json` serializes the title-filtered QuerySet into Django's JSON format. Each record contains `model`, `pk`, and `fields`. `show_projects` calls that function directly and deserializes its response into Project instances for `projects.html`. There is no HTTP request from the server to itself and no browser-side JavaScript fetch. This deliberately redundant round trip follows the tutorial's data-delivery exercise; the model's properties and featured ordering still work. The optional XML endpoint exposes the same records in a second representation. [Django serialization documentation](https://docs.djangoproject.com/en/6.1/topics/serialization/)

The search parameter is `title`, for example `/api/projects/?title=macan`. It searches project titles rather than organization names. A whitespace-only query returns all records; an unmatched query produces an empty result without deleting anything.

Deletion opens a native HTML popover. Cancel, Escape, or clicking outside dismisses it. The confirmation form sends a POST with a CSRF token. A GET to the deletion URL returns 405 and does not delete data; a POST for a missing UUID returns 404. The popover is not declared an ARIA modal, because native popovers do not make the rest of the page inert. [MDN popover reference](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/popover)

The existing PWS HTTPS origin is listed in `CSRF_TRUSTED_ORIGINS`; the CSRF middleware stays enabled. Forms use the existing English labels and warm portfolio colors. The two optional URL/image fields from the tutorial example are not part of this model, so no unused image or external-link inputs are added.

## AI Usage Disclosure

I used **ChatGPT** . Assistance included explanations, substantial HTML/CSS and Python code suggestions fixture content, tests, debugging, Git commands, and README drafting.





The code and documentation were developed with AI assistance. Thus for example the development of this specific README could easily facilitated. My contribution included selecting and checking the personal content, applying changes, running migrations and tests, inspecting the site, and reporting problems that required another iteration.


### Further Development

Useful next steps would be authentication and authorization for changes, editing existing projects, topic filters, and database models for education and skills. Reproducible dependency versions would also make environment setup more predictable. These are possible future improvements rather than features claimed in the current implementation.
