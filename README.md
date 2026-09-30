# Marcel Mikula — Personal Portfolio

A responsive personal portfolio developed for Platform-Based Programming at the Faculty of Computer Science, Universitas Indonesia.

The project started as a static About Me page. Tutorial 2 introduced database-backed experience entries; Assignment 2 added a project overview, individual project pages, and reusable page templates. Tutorial 3 adds project creation, title search, JSON/XML data delivery, and deletion with confirmation. Assignment 3 adds database-backed education with create/update forms, deletion, filtering, and JSON delivery, and also exposes experience as JSON. Tutorial 4 adds registration, login/logout, session and cookie handling, owner-only changes, and project stars. Assignment 4 extends Education with an Editor role, personal stars, a favourites filter, and public detail pages. Tutorial 5 loads and searches projects with JavaScript, adds projects through an AJAX popover form, and provides reusable toast notifications.

[Assignment 1 specification](https://pbp.cs.ui.ac.id/en/assignments/individual/tugas-1.html) · [Assignment 2 specification](https://pbp.cs.ui.ac.id/en/assignments/individual/tugas-2.html) · [Assignment 3 specification](https://pbp.cs.ui.ac.id/en/assignments/individual/tugas-3.html) · [Assignment 4 specification](https://pbp.cs.ui.ac.id/en/assignments/individual/tugas-4.html)

## Student Information

- **Name:** Marcel Mikula
- **NPM:** 2606816592
- **Class:** PBP A

## Current Features

- Profile, a database-backed education overview, and Data & AI topics on the home page
- Dedicated Education page with create/edit forms, deletion confirmation, text search, status filtering, and result counts
- Database-backed project overview featuring Porsche, ING, and my bachelor's thesis
- Individual project pages with a return link to the overview
- Database-backed B. Braun experience with responsibilities, role progression, and employment period
- Shared navigation, footer, stylesheet, and skip link through `base.html`
- Responsive layouts, keyboard focus indicators, and reduced-motion support
- Native expandable project contributions using `<details>` and `<summary>`
- Empty states for the project and experience lists
- A 404 response for a project ID that does not exist
- Versioned fixtures for loading three projects, one experience entry, and three education entries
- A model-based project form with validation, CSRF protection, and success messages
- Project title search and JSON/XML endpoints with the same filter
- A native popover for confirming deletion through a CSRF-protected POST
- Education validation for study periods, required fields, website URLs, and display order
- Project cards loaded from JSON with `fetch()`; Education and Experience retain their server-side JSON-to-template flow
- Live project search with a 300 ms debounce, request cancellation, loading/error states, and retry
- Owner-only AJAX creation, inline form errors, and reusable success/error toast notifications
- Escaped card content and plain-text form cleaning for XSS protection
- Registration and login using Django's built-in forms, with the visiting account shown separately from the portfolio owner's name
- A last-login cookie displayed on Home and removed on logout
- Public portfolio pages; project creation/deletion and education creation/deletion restricted to the owner
- Education editing available to the owner and members of the Admin-managed `Editor` group
- Education stars with per-account state, counts, feedback, and a My starred entries filter
- Public education detail pages and consistent permission-aware controls
- Education JSON retains its public fields without exposing star membership or account details
- Project stars for signed-in accounts, with counts, usernames, and an unstar action
- 105 Django tests and 13 JavaScript tests covering the portfolio, forms, permissions, AJAX, and security boundaries (execution status below)

The frontend uses HTML5, CSS3, vanilla JavaScript modules, and Django Template Language. It uses CSS Grid, Flexbox, CSS variables, and `clamp()`; no frontend framework or JavaScript library is required.

## Pages and Navigation

| Page or section | URL | Content |
| --- | --- | --- |
| Home | `/` | Profile, education, and Data & AI |
| Register | `/register/` | Create an ordinary visitor account, then redirect to Login |
| Login | `/login/` | Authenticate, set session and last-login cookie, then redirect to Home |
| Logout | `/logout/` | CSRF-protected POST; clear session and last-login cookie |
| Star / unstar project | `/projects/<uuid>/star/` | CSRF-protected POST; requires a signed-in account |
| Projects | `/projects/` | Browser fetches and displays project records from JSON |
| Title search | `/projects/?title=macan` | Case-insensitive matching on project titles |
| Add project | `/projects/add/` | Original full-page owner form remains available |
| Add project with AJAX | `/projects/add-ajax/` | Owner-only POST; JSON 201 on success, 400 on invalid input, 403 without permission |
| Projects as JSON | `/api/projects/` | Records plus star count, session-specific state, and local action URLs; supports `?title=...` |
| Projects as XML | `/api/projects/xml/` | The same records and filter represented as XML |
| Delete project | `/projects/<uuid>/delete/` | POST only; linked through the confirmation popover |
| Project detail | `/projects/<uuid>/` | One selected project |
| Experience | `/experience/` | Professional experience from the database |
| Education | `/education/` | Education records; supports `?q=...&status=current` or `completed` |
| Education detail | `/education/<uuid>/` | Public entry details, star status, and permitted actions |
| Star / unstar education | `/education/<uuid>/star/` | Signed-in users; CSRF-protected POST |
| My starred education | `/education/?starred=1` | Current account's favourites; combines with `q` and `status` |
| Education overview | `/#education` | Unfiltered overview of the same database records on the home page |
| Add education | `/education/add/` | GET displays the form; valid POST creates an entry |
| Edit education | `/education/<uuid>/edit/` | GET prefills the form; valid POST updates that record |
| Delete education | `/education/<uuid>/delete/` | POST only, after confirmation |
| Education as JSON | `/api/education/` | Public fields; text/status filters and session-based `starred=1` filter |
| Experience as JSON | `/api/experience/` | Experience records, including UUIDs and historical dates |
| Skills | `/#skills` | Data & AI section on the home page |

The navigation uses named Django URLs. Education now opens its own page. Profile and Skills link to home-page sections; existing `/#education` links continue to work. Changes to an education record appear both on the dedicated page and in the home overview.

## Technologies and Development Environment

The recorded local test environment uses **Python 3.13.9**, **Django 6.1**, and **SQLite** on macOS. Dependencies are listed in `requirements.txt`, including WhiteNoise and python-dotenv. That file currently leaves dependency versions unpinned, so a later installation may resolve different versions.

## Project Structure

| Path | Responsibility |
| --- | --- |
| `portofolio/settings.py` | Project configuration, database selection, templates, and static files |
| `portofolio/urls.py` | Project-level routing, including the `main` application's URLs |
| `main/models.py` | `Experience`, `Project`, and `Education`, including education period validation |
| `main/forms.py` | `ProjectForm` and `EducationForm`, with explicit editable-field lists |
| `main/views.py` | Page views, form submission handlers, filtering, and JSON/XML responses |
| `main/permissions.py` | Shared Education owner/editor predicates and UI access context |
| `main/tests_tutorial4.py` | Authentication, session/cookie, project-star and permission tests |
| `main/tests_assignment4.py` | Four-role checks, Admin assignment, Education stars, API privacy and query cost |
| `main/tests_tutorial5.py` | AJAX contracts, roles, CSRF, query cost, and text cleaning |
| `tests/js/tutorial5.test.js` | Card escaping, debounce, stale responses, request errors, CSRF, and toast timers |
| `main/urls.py` | Named routes in the `main` namespace |
| `main/tests.py` | Automated model, page, and fixture tests |
| `main/tests_tutorial3.py` | Creation, deletion, CSRF, filtering, JSON, and XML tests |
| `main/tests_assignment3.py` | Education CRUD, validation, serialization, shared layouts, and fixture tests |
| `main/migrations/` | Versioned database schema changes |
| `main/fixtures/main/projects.json` | Three portfolio project records |
| `main/fixtures/main/experience.json` | The B. Braun experience record |
| `main/fixtures/main/education.json` | Universitas Indonesia, TU Darmstadt, and Mannheim education entries |
| `templates/base.html` | Shared document structure, navigation, footer, and content block |
| `templates/index.html` | Profile, education, and Data & AI content |
| `templates/projects.html` | Project-list shell, search, feedback states, and safe JSON configuration |
| `templates/components/project_form_modal.html` | Owner-only creation popover using the existing ProjectForm |
| `templates/components/toast.html` | Reusable manual notification popover |
| `templates/projects_form.html` | Project creation form, help text, and validation errors |
| `templates/components/project_delete_modal.html` | Earlier server-rendered project confirmation wrapper, retained for reuse |
| `templates/components/delete_confirmation.html` | Server-rendered Education confirmation; JavaScript cards preserve the same pattern |
| `templates/components/form_fields.html` | Shared labels, widgets, help text, and field errors |
| `templates/components/education_card.html` | Education card shared by the home overview and education page |
| `templates/education.html` | Education list, filters, actions, and empty states |
| `templates/education_detail.html` | Public Education detail page using the shared card |
| `templates/components/education_star.html` | CSRF-protected star control, count, state and return filters |
| `templates/components/education_access.html` | Current role and available Education actions |
| `templates/education_form.html` | Shared create/update education form page |
| `templates/project_detail.html` | Individual project content |
| `templates/experience.html` | Experience list and empty state |
| `static/css/style.css` | Shared styling and responsive rules |
| `static/css/tutorial3.css` | Form, search, message, and confirmation styles using the existing design tokens |
| `static/css/assignment3.css` | Education cards, action layout, and status-filter styling |
| `static/css/tutorial4.css` | Authentication navigation, login/register forms and star buttons |
| `static/css/assignment4.css` | Education role panel, stars and detail-page layout |
| `static/css/tutorial5.css` | Creation popover, toast and AJAX feedback styles |
| `static/js/projects.js` | Browser events, card rendering, form feedback, and list refresh |
| `static/js/project-utils.js` | Escaping, card markup, debounce, fetch controller, and AJAX submission |
| `static/js/toast.js` | Reusable notifications using textContent and cancellable timers |
| `package.json` | Optional dependency-free Node test command; no frontend build step |
| `static/img/Download.jpeg` | Profile photograph |
| `manage.py` | Django management commands |

## Local Setup

These instructions are for a fresh checkout of the Tutorial 5 branch after it has been pushed. Install Python 3.13 and Git first. Node.js 22+ is optional for the additional JavaScript unit tests; it is not needed to run Django.

1. Clone the branch and enter the repository:

   ```bash
   git clone --branch feature/tutorial_5_ajax https://github.com/Marcelm1806/myportofolio.git
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
   python manage.py loaddata main/education.json
   ```

   On an empty database, the fixture commands install three projects, one experience record, and three education entries. When upgrading an existing database, run only `migrate`: do not reload fixtures over your edited records. Migrations 0005 and 0006 add the Project and Education star relationship tables and do not replace portfolio records. Tutorial 5 adds no model fields or migrations. Without initial data, the corresponding pages display their empty states.

   Create the portfolio owner's account if you do not already have a superuser:

   ```bash
   python manage.py createsuperuser
   ```

   Choose credentials locally. The Register page creates ordinary visitor accounts, never owner accounts. Accounts and passwords are not included in Git or in the portfolio fixtures. To try the Editor role, register a second ordinary account and assign it to the `Editor` group through Django Admin as described under Assignment 4 below.

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

   The stylesheet links include a version query parameter so the browser requests the current CSS after this update. If a page still looks unstyled, hard-refresh it (`Cmd + Shift + R` on macOS) and use `python manage.py findstatic css/style.css --verbosity 2` to check which local file Django resolves. The featured project should be a dark card, education entries should use cards, and the home page should have a dark Data & AI section. The photograph reserves space for its decorative offset on narrow screens, and the small role, username, and award labels use dark text on the light accent background.

## Portfolio Data and Design Decisions

### Models

`Project` stores short labels in `CharField` fields and longer summaries, contributions, and technology lists in `TextField` fields. A `BooleanField` marks featured work; a `PositiveIntegerField` controls display order. Each project has a UUID primary key used in its detail URL.

The model's default ordering places featured projects first, then uses `display_order` and `title`. The `technology_list` property splits the stored technology text into trimmed, non-empty lines for display as tags.

`Experience` stores the role title, organization, category, role timeline, responsibilities, and dates. Its `responsibility_list` property converts description lines into list items. An absent end date produces the ongoing status.

Employment dates in the B. Braun fixture are known to month precision. Their day component is normalized to 1, and the page displays only month and year. `started_at` uses `default=timezone.now`, allowing an explicit historical start date to be supplied when creating a record. [Django field reference](https://docs.djangoproject.com/en/6.1/ref/models/fields/#django.db.models.DateField.auto_now_add)

`Education` uses text fields for the institution, degree, and optional description; integer fields for the study years and display order; a boolean for ongoing study; and an optional URL. Django generates its UUID and creation/update timestamps. Year precision preserves the known portfolio history without inventing exact dates. The initial UI exchange and TU Darmstadt degree are marked as ongoing; Mannheim is recorded as 2020–2025. The fixed timestamps in the education fixture describe the seed records, not study dates.

The model's `clean()` method rejects an end year before the start year, an end year on a current entry, or a completed entry without an end year. Year validators accept 1900–2100. `EducationForm` runs these checks for both creation and editing. Direct ORM `save()` calls do not automatically call `full_clean()`, so scripts that bypass the form must validate explicitly.

### Loading and Updating Data

The JSON fixtures are a reproducible source for the initial portfolio records. Views retrieve the imported records through the ORM. JavaScript renders the Project JSON as cards; the other sections use Django templates.

Fixture entries have fixed UUIDs. Loading the same fixture again updates those entries instead of creating additional copies. It also restores their fields to the fixture values, overwriting edits to those same records. Separately created records with different IDs are preserved. [Django fixture documentation](https://docs.djangoproject.com/en/6.1/howto/initial-data/)

To update the versioned portfolio content, edit the relevant fixture and reload it. The local SQLite database, virtual environment, and environment files are excluded from Git; migrations and fixtures are the files needed to rebuild the schema and initial portfolio data.

### Current Scope

Projects, experience, and education are rendered from database records. Profile values come from the view; skills remain static. Education can be created, updated, deleted, and filtered in the browser. Projects retain their Tutorial 3 creation, deletion, title search, JSON/XML, and detail features. Tutorial 5 moves list rendering and creation from page reloads to browser-side requests; star and delete remain CSRF-protected HTML POST forms. Project editing and experience editing remain outside this assignment's scope.

Tutorial 4 provides authentication and session/cookie handling. Assignment 4 permits registered accounts to star/unstar Education as well as Projects. Education updates require the owner or membership of `Editor`; creating/deleting Education and creating/deleting Projects remain owner-only. `is_staff` alone grants none of these portfolio write actions. The views enforce the rules, and template controls reflect those same rules. CSRF remains enabled for state-changing forms.

## Testing and Verification

The previously recorded Tutorial 3 result was **28 passing tests** on my Mac. Assignment 3 added **22 test cases**, bringing that suite to **50**, and its local checks were reported successful. Tutorial 4 added **22 further tests**, taking the suite to **72**. Assignment 4 adds **20 tests**, bringing that version to **92**. Existing write tests now authenticate as the owner; their original form and data assertions remain in place. In the Tutorial 4 patch preparation environment, Django 6.1.1 ran all **72 tests successfully**, the system check found no issues, and the migration check reported no pending model changes. An upgrade from migration 0004 to 0005 preserved every existing field of the three projects, one experience, and three education fixtures. These checks were run separately from my Mac. Browser verification is separate from those automated preparation results.

The Assignment 4 preparation run passed **all 92 tests** on Django 6.1.1. `check` reported no issues and `makemigrations --check --dry-run` reported no changes. Upgrading from 0005 to 0006 preserved all fields of the three Education, three Project and one Experience records, plus an existing Project star. The development server returned HTTP 200 for Home, Projects, Experience, Education, an Education detail page, the Education API and the new stylesheet. Those were separate preparation checks. Assignment 4 was subsequently applied and pushed as commit `a6ee42a217d1301ce1e8dff277f84bd1c4725b7b`, and I reported that the appearance looked correct.

Tutorial 5 adds **13 Django tests**, for **105 passing tests**, and **13 passing JavaScript unit tests**. The preparation environment used Python 3.12.14, Django 6.1.1, and Node.js 24.19.0. The configuration check found no issues and the migration dry run found no changes. A development-server smoke check returned HTTP 200 for Home, Projects, Experience, Education, both tested Project JSON queries, and the new CSS/JavaScript assets with the expected MIME types. GET on the creation endpoint returned 405 as intended. Earlier Project tests were adapted to assert the new JSON/card flow; authorization and data-preservation checks remain. JavaScript tests exercise rendering/escaping, debounce, stale response prevention, error handling, CSRF submission, and toast replacement. These results do not claim a browser layout test or verification on my Mac. Tutorial 5 browser checks remain pending after patch application.

| Test group | Count | Coverage |
| --- | --- | --- |
| Tutorial 2 tests | 6 | Home and experience pages, navigation, missing page, model behavior, empty experience list, and completed status |
| Project list tests | 3 | Project content and template, empty state, and links from existing pages |
| Project detail tests | 3 | Selected project content, missing project ID, and detail links from the list |
| Project fixture test | 1 | Loading twice without duplicates while preserving an independently created project |
| Experience history test | 1 | Saving and displaying historical dates, organization, timeline, and responsibilities |
| Tutorial 3 write tests | 9 | Creation, invalid input, redirect behavior, preservation of other records, CSRF, deletion, missing IDs, and HTTP methods |
| Tutorial 3 data-delivery tests | 5 | JSON structure and ordering, shared title filtering, distinct empty states, XML content, and read-only endpoints |
| Education write tests | 11 | Create/update/delete, preservation of other records, invalid input, generated-field protection, missing IDs, methods, and CSRF |
| Education data tests | 9 | Typed JSON, actual JSON-to-template flow, filters, empty states, home synchronization, escaping, shared layouts, and experience JSON |
| Education fixture and period tests | 2 | Repeatable fixture loading, model validation, preservation of independent entries, and year labels |
| Tutorial 4 authentication tests | 12 | Registration, password validation/hashing, session persistence, login/logout cookies, inactive accounts, CSRF, and escaped cookie display |
| Tutorial 4 authorization and star tests | 10 | Visitor redirects, ordinary/staff denial, owner controls, independent stars, HTTP methods, CSRF, missing IDs, and natural-key serialization |
| Assignment 4 permissions | 9 | Four roles, direct URL denial, editor validation, control visibility, role revocation, forged role input, Admin assignment and project boundaries |
| Assignment 4 stars | 7 | Independent membership, CSRF, methods, missing IDs, safe return paths, filter feedback and account deletion |
| Assignment 4 data and rendering | 4 | API field allowlist, private per-account filtering, public detail pages and one-query star aggregation |
| Tutorial 5 AJAX | 13 | List shell, JSON star state, constant query cost, owner creation, role denial, validation, CSRF, and input cleaning |
| Tutorial 5 JavaScript (Node) | 13 | Escaped cards and URLs, debounce, request races, HTTP errors, submission and toast timers |

Run the full suite and development checks with:

```bash
python manage.py test
python manage.py makemigrations --check --dry-run
git diff --check
```

The recorded Assignment 2 results were 14 passing tests, `No changes detected`, and no whitespace errors. That local test run also printed a warning about the missing collected `staticfiles/` directory; the test suite completed successfully. The full Tutorial 3 test suite subsequently completed successfully: 28 tests passed. Assignment 3 adds `0004_education.py`; it must be applied before starting the updated site.

Optional JavaScript checks, with Node.js 22+ and no package installation:

```bash
node --test tests/js/*.test.js
```

Django tests run against a separate test database. Example names used in test cases are test data. These checks exercise model behavior and rendered HTTP responses; they do not measure browser layout or verify the truth of portfolio claims.

For a manual browser check:

- Open Home, Projects, Experience, and Education, and follow each project detail link.
- Expand and collapse the contribution sections, and follow the return link from a detail page.
- Check desktop and narrow mobile widths, including approximately 390 pixels, for readable content and horizontal overflow.
- Use the keyboard to follow navigation and the skip link.
- Confirm that the three projects and the B. Braun responsibilities match the intended content.
- Add a temporary project, search for its title, inspect the filtered JSON/XML, cancel deletion once, and then delete only that temporary record.
- Check that invalid form input shows errors and retains the entered values. Refresh after a successful submission and confirm that it does not create another record.
- Create a temporary education entry, edit it, and confirm the changes on both Education and Home. Check current/completed status filters and `/api/education/?q=...`.
- Try an end year earlier than the start year, then cancel deletion once and finally delete the temporary entry. Confirm the three real entries remain.
- Inspect `/api/experience/` and confirm that the experience page still displays B. Braun correctly.

## Weekly Progress

| Stage | Progress |
| --- | --- |
| Tutorial 0 | Created the repository, configured Git, prepared the virtual environment, and initialized Django. |
| Tutorial 1 | Built the About Me page with profile information, a photograph, and external links. |
| Assignment 1 | Added static projects, experience, education, and skills; implemented responsive styling and native interactive details. |
| Tutorial 2 | Introduced the `main` app, the `Experience` model, ORM-backed views, named URLs, migrations, and six tests. |
| Assignment 2 | Added the `Project` model and migration, project list and detail pages, shared templates, fixtures, and additional tests. Restored the B. Braun content as database records and extended experience fields. |
| Tutorial 3 | Added a Project ModelForm, title search, JSON/XML endpoints, the tutorial's JSON-to-template flow, POST-only deletion with confirmation, success messages, and 14 additional tests. |
| Assignment 3 | Added Education with all CRUD actions, JSON delivery, text/status filtering, a synchronized home overview, shared form/card/confirmation components, experience JSON, a schema migration, fixture, and 22 additional tests. Local configuration, migration, test-suite, and browser checks completed successfully. |
| Tutorial 4 | Added registration, login/logout, login status, a last-login cookie, superuser-only changes, project stars with a many-to-many migration, natural-key API output, and 22 tests. Local browser verification follows patch application. |
| Assignment 4 | Added the Admin-managed Editor role, Education stars, public details, a personal star filter, shared role checks, private API output and 20 tests; applied and pushed, with appearance checked locally. |
| Tutorial 5 | Added AJAX project loading and creation, live search, toast feedback, safe rendering, and 13 Django plus 13 JavaScript tests. Local browser verification follows patch application. |

## Reflective Questions

The Assignment 1 and Assignment 2 answers below describe their respective submitted versions. Tutorial 3 subsequently changed the project-list data flow, and Assignment 3 moved education into a model, as explained below; it does not change those historical submissions.

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

This section records the Tutorial 3 baseline; Tutorial 5 later replaces its Project list data flow. The implementation adapts [Tutorial 3](https://pbp.cs.ui.ac.id/en/tutorial/tutorial-3.html) to the existing portfolio. `ProjectForm` uses `organization`, `summary`, `contribution`, `technologies`, and the other existing fields. It does not introduce the tutorial example's differently named fields. `base.html` already supplies the document structure and the single `<main>` element; child templates fill its `content` block and use the existing `title` block.

On GET, `create_project` displays an unbound form. On POST, it binds the submitted data, validates it, saves one new record if valid, and redirects to the project list. Invalid input renders the same bound form with errors and the submitted values. An explicit method check binds even an empty POST so required-field errors are shown. [Django ModelForm documentation](https://docs.djangoproject.com/en/6.1/topics/forms/modelforms/)

`get_projects_json` serializes the title-filtered QuerySet into Django's JSON format. Each record contains `model`, `pk`, and `fields`. `show_projects` calls that function directly and deserializes its response into Project instances for `projects.html`. There is no HTTP request from the server to itself and no browser-side JavaScript fetch. This deliberately redundant round trip follows the tutorial's data-delivery exercise; the model's properties and featured ordering still work. The optional XML endpoint exposes the same records in a second representation. [Django serialization documentation](https://docs.djangoproject.com/en/6.1/topics/serialization/)

The search parameter is `title`, for example `/api/projects/?title=macan`. It searches project titles rather than organization names. A whitespace-only query returns all records; an unmatched query produces an empty result without deleting anything.

Deletion opens a native HTML popover. Cancel, Escape, or clicking outside dismisses it. The confirmation form sends a POST with a CSRF token. A GET to the deletion URL returns 405 and does not delete data; a POST for a missing UUID returns 404. The popover is not declared an ARIA modal, because native popovers do not make the rest of the page inert. [MDN popover reference](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/popover)

The existing PWS HTTPS origin is listed in `CSRF_TRUSTED_ORIGINS`; the CSRF middleware stays enabled. Forms use the existing English labels and warm portfolio colors. The two optional URL/image fields from the tutorial example are not part of this model, so no unused image or external-link inputs are added.

## Assignment 3: Education Forms and JSON Delivery

The additional portfolio section is **Education**. Its model has eight editable fields with several types (`CharField`, `TextField`, `PositiveIntegerField`, `BooleanField`, and `URLField`), plus a generated UUID and timestamps. `EducationForm.Meta.fields` lists every editable field and excludes `id`, `created_at`, and `updated_at`. This resolves the assignment wording about ID/timestamp fields: they exist on the model but are not user inputs.

| Requirement | Implementation |
| --- | --- |
| Shared root template | Every full page extends `base.html`; components are included fragments, not separate documents |
| Create and update forms | `EducationForm`, `create_education`, and `update_education`, sharing one form template |
| Delete action | `delete_education`, POST only, with CSRF and a confirmation popover |
| JSON retrieval | `get_education_json` at `/api/education/` |
| Deserialize before display | `show_education` calls the JSON view and passes deserialized Education instances to the template |
| Consistent page content | The home overview also reads Education data through JSON serialization/deserialization |
| Additional existing data as JSON | `/api/experience/`; the experience page also deserializes its JSON response |

The education page and API share text and status filters. Search matches institution or degree, ignoring case and surrounding whitespace. Status accepts `current` or `completed`; an unknown value is treated as no status filter. The default ordering uses `display_order`, newest start year, institution, and UUID as a stable tie-breaker. GET requests never save records.

Create and update share `_education_form_response()`. For updating, the view looks up the UUID with `get_object_or_404()` and supplies `instance=entry` to the form. `form.save()` therefore updates that row rather than inserting a duplicate. Invalid submissions retain their input and show field errors. A successful POST redirects to the list and shows a success message, so refreshing the resulting page does not repeat the submission.

Additional usability features include combined search/status filtering, result counts, separate empty/no-match states, adjustable display order, visible validation feedback, keyboard-accessible confirmation controls, and immediate consistency between the two education views. The site continues to use the existing responsive design and native HTML controls without a frontend framework.

### Assignment 3

1. **Why use ModelForm rather than hand-written forms, and why include a CSRF token?**

   `ModelForm` connects the form to a model so field types, required values, length limits, and validators do not need to be recreated independently in HTML and Python. My `EducationForm` adds readable labels, help text, and widgets while obtaining its validation and persistence behavior from `Education`. The shared form-fields template still controls the HTML layout; using ModelForm does not mean giving up custom styling.

   On submission, `is_valid()` checks field values and the model's study-period rules before `save()` is called. For editing, `instance=entry` preserves the selected record's identity. Explicitly listing editable fields also prevents submitted UUID or timestamp values from becoming writable through this form.

   Each POST form includes `{% csrf_token %}`. Django's CSRF middleware checks the submitted token and applicable origin information to reduce the risk of another website causing a visitor's browser to submit an unwanted action. This applies to creation, editing, and deletion. A missing or invalid token is rejected. CSRF protection is distinct from authentication and permission checks; that Assignment 3 version did not yet restrict editing to an authenticated owner; Tutorials 4 and Assignment 4 added the access rules documented below.

2. **Why is JSON often preferred to XML in modern web applications?**

   JSON represents common application values directly as objects, arrays, strings, numbers, booleans, and null. This matches the structure of my education records: a year is a number, `is_current` is a boolean, and an absent end year is null. Browsers and many programming languages provide JSON parsers, making it convenient for APIs and browser clients.

   Compared with equivalent XML containing repeated opening and closing tags, JSON often needs less markup. It is not always smaller or faster, and it is not limited to JavaScript. XML remains useful where document structure, namespaces, schema tooling, or an existing XML-based integration matters. The project still exposes the Tutorial 3 XML endpoint; Education uses JSON to follow the assignment's workflow.

3. **How does a view return portfolio data as JSON, and why serialize models?**

   A GET request to `/api/education/` is resolved by the project and application URL configurations to `get_education_json`. `_filtered_education()` constructs an ordered QuerySet using the query parameters. Django's serializer evaluates those records and converts them to JSON containing each object's model label, primary key, and fields. The view returns this text in an `HttpResponse` with `Content-Type: application/json`.

   A Python QuerySet or model instance cannot be transferred directly as a JSON response. Serialization turns framework objects and values such as UUIDs and timestamps into a transport representation that another client can parse. It exposes the serialized model fields; computed properties such as `period_label` are not separate stored fields in this response.

   For `/education/`, `show_education` calls the JSON view directly as a Python function and deserializes its response. `_objects_from_json()` takes the reconstructed objects and passes them to `education.html`, where properties such as `period_label` work again. The helper never saves those objects. There is no server-to-itself HTTP request and no browser-side fetch. This round trip intentionally demonstrates the week's serialization exercise; an ordinary server-rendered view could otherwise pass a QuerySet directly to its template.

## Tutorial 4: Authentication, Sessions, Cookies, and Authorization

This section describes the Tutorial 4 baseline; Assignment 4's extension follows below. The implementation follows [Tutorial 4](https://pbp.cs.ui.ac.id/en/tutorial/tutorial-4.html), adapted to the existing Assignment 3 portfolio. `UserCreationForm` hashes passwords and applies the configured password validators. `AuthenticationForm` validates credentials; `login()` records the account in Django's session. The session cookie identifies the visitor, while `PROFILE` still identifies Marcel as the portfolio owner.

Successful login sets a separate `last_login` cookie, formatted in UTC, which Home reads through `request.COOKIES`. This display cookie never grants access. Logout clears the session and deletes the cookie without deleting the account or its stars. The cookie uses `HttpOnly`, `SameSite=Lax`, and `Secure` when `DEBUG=False`. Login returns to Home, as in the tutorial; it does not follow the `next` parameter.

| Account | Read pages and APIs | Star/unstar projects | Add/delete projects; manage education |
| --- | --- | --- | --- |
| Anonymous visitor | Yes | Redirect to Login | Redirect to Login |
| Registered account | Yes | Yes | 403 Forbidden |
| Staff account without superuser status | Yes | Yes | 403 Forbidden |
| Superuser / portfolio owner | Yes | Yes | Yes |

`login_required` protects write views, followed by an explicit `is_superuser` check where owner access is required. The existing education forms receive the same protection so they do not remain publicly writable. Hidden buttons only reflect these server-side checks. In the Tutorial 4 baseline, Education was owner-only; Assignment 4 below deliberately extends update access and adds its own stars.

`Project.starred_by` is a many-to-many relationship to `settings.AUTH_USER_MODEL`, with reverse name `starred_projects`. Migration `0005_project_starred_by` adds the relationship table while keeping existing projects, education, and experience intact. The toggle endpoint uses only `request.user`, never a submitted account ID. Each account can add or remove its own star independently. The count remains visible on mobile, and the title hint lists usernames.

Project JSON and XML use `use_natural_foreign_keys=True`: the public relationship contains usernames rather than numeric account IDs. No password hashes or other account fields are serialized. The existing title filter and JSON-to-template data flow are retained. Merely loading a page does not save deserialized objects.

At the Tutorial 4 stage, all changes used standard HTML forms and CSRF tokens without JavaScript. Tutorial 5 now uses AJAX for project creation; the existing full-page form, star/unstar, and logout still work through standard POST forms. Logout is a POST button in the navbar, and star/unstar is POST-only. These are deliberate adjustments to the tutorial's GET logout example and its harmless-GET star handler: visiting a URL alone cannot change state. The optional Selenium example would need to click the Logout button instead of requesting `/logout/` with GET. Selenium and Burp Suite are optional and are not added as runtime dependencies.

For local verification after applying the patch:

1. Run `python manage.py migrate`, `python manage.py check`, `python manage.py test`, and `python manage.py makemigrations --check --dry-run`.
2. As a visitor, open Home, Projects, Experience, and Education. Login/Register should appear; management controls should not. Clicking Star should lead to Login.
3. Register an ordinary account. Try mismatching passwords and an existing username, then log in successfully. Confirm that the navbar shows the visitor username while the profile still shows Marcel.
4. Inspect `sessionid`, `last_login`, and `csrftoken` in browser storage. Confirm the timestamp on Home. Use Logout and verify the session and timestamp cookie are removed.
5. As the ordinary account, star/unstar a project, check the count and `/api/projects/`, and confirm `/projects/add/` returns 403. Try a second account to confirm independent stars.
6. Log in with your superuser. Add/delete a temporary project and create/edit/delete a temporary education entry. Preserve the actual portfolio records.
7. Check the navigation and forms at desktop and mobile widths. If CSS is cached, use a hard refresh.

## Assignment 4: Education Roles and Stars

Education is the section continued from Assignment 3. Authentication remains Django's built-in system from Tutorial 4; no custom account model or public role-selection form is introduced.

| Account | Read list/detail/API | Star/unstar | Edit Education | Add/delete Education |
| --- | --- | --- | --- | --- |
| Visitor | Yes | Login redirect | Login redirect | Login redirect |
| Member | Yes | Own star | 403 | 403 |
| Editor group member | Yes | Own star | Yes | 403 |
| Owner / superuser | Yes | Own star | Yes | Yes |

The role panel and visible controls use the same predicates as the write views in `main/permissions.py`. Hiding controls is a convenience; direct requests still receive the appropriate redirect or 403. The case-sensitive group name is `Editor`. Staff status alone does not imply membership, and an Editor does not need staff status. Removing membership revokes editing on the next request.

### Set up the Editor role through Django Admin

1. Apply migrations and create the owner with `python manage.py createsuperuser` if a superuser does not already exist.
2. Use `/register/` to create a separate ordinary account for trying the Editor workflow. Do not reuse a superuser to test restricted permissions.
3. Log in to `/admin/` with the owner account. Under **Authentication and Authorization → Groups → Add**, enter exactly **Editor** and save. If it already exists, reuse it. No extra permissions need to be selected because this implementation explicitly checks group membership.
4. Under **Users**, open the ordinary account. Move **Editor** into its chosen groups and save. Keep **Staff status** and **Superuser status** unchecked; keep the account active.
5. Log into the portfolio with that account. Education now shows **Editor** and Edit controls, while Add/Delete stay hidden. The account cannot enter Django Admin or change anyone's roles.

Role creation and assignment are manual database operations through Admin. No migration, fixture, public form, or request parameter assigns a role or creates an account/password. Each fresh database therefore needs its own owner and optional Editor setup.

### Data, interaction, and API decisions

Migration `0006_education_starred_by` adds `Education.starred_by`, a many-to-many relationship to `settings.AUTH_USER_MODEL`. The generated intermediary table permits one relationship per user and education entry. `/education/<uuid>/star/` accepts only POST with CSRF protection, and uses `request.user` to add or remove that user's membership. It never accepts another account ID as the actor. Refreshing the redirected GET does not toggle again.

List and detail cards expose a star count and the current user's state through button text and `aria-pressed`. Success messages confirm the change. The **My starred entries** filter combines with the existing institution/degree search and current/completed status filter. A star submission preserves those filters; removing the last matching star shows a specific empty state. Detail-page stars return to that detail page. Return destinations are constructed from known local routes and allowed filter values, never an arbitrary submitted URL.

`/api/education/` keeps Assignment 3's Django serializer structure (`model`, `pk`, `fields`) and its original ten public fields. An explicit `fields` allowlist excludes `starred_by`, user IDs, usernames, passwords, emails, and account permissions. The optional `starred=1` filter uses only the current session account; it returns `[]` for visitors. The response varies on Cookie so caches can distinguish personalized requests. Tutorial 4's Project JSON/XML continue to use the tutorial's username-based natural keys; this stricter Education API does not expose star membership.

The Education list still calls the JSON view and deserializes its response, preserving the earlier assignment's required data flow. A single aggregate query then adds counts and per-account booleans to all displayed objects. This avoids querying a user collection for every card. The aggregate data is display-only; deserialized instances are never saved. Detail pages are publicly readable at `/education/<uuid>/`, with 404 for unknown UUIDs and 405 for state-changing methods.

### Assignment 4

The official English page still contains a placeholder rather than specific reflective questions as of September 28, 2026. The following are implementation notes and self-reflection, not invented official questions.

1. **Authentication and authorization are separate.** Login proves which account is making the request. The Education access rules then decide which actions that account may perform. The `last_login` cookie is display data, not evidence of ownership or Editor membership. A forged role field or cookie cannot grant permission.
2. **Roles must match both the server and interface.** Group membership lets the owner delegate editing without granting creation, deletion, or account administration. Shared predicates reduce the risk of showing a button that its corresponding view refuses, or permitting an operation whose button happens to be hidden.
3. **CSRF protection, explicit form fields, and API filtering address different problems.** CSRF checks protect authenticated state-changing requests. The ModelForm's editable-field list prevents overwriting star membership through an edit form. The serializer's allowlist keeps account relationships out of a public data endpoint. None of these substitutes for the role check.

### Review after applying the patch

- Run `python manage.py migrate`, `python manage.py check`, `python manage.py test`, `python manage.py makemigrations --check --dry-run`, and `git diff --check`. Do not reload portfolio fixtures over edited records.
- With no login, open Home, Education, a detail page, and `/api/education/`. Confirm that Star requires login and write controls are absent.
- As an ordinary member, star and unstar an entry. Try the personal filter and a second account. A direct visit to an edit/add form must return 403.
- Create the Editor group and assign membership in Admin. As that Editor, edit a temporary entry, try an invalid study period, and verify that create/delete requests are denied. Remove the membership in Admin and confirm editing stops.
- As the owner, create, edit, and delete a temporary entry. Verify the same existing portfolio records still appear on Home and Education.
- Check desktop and mobile layout, keyboard focus, the selected star state, filter preservation, and the back link on details. Browser checks on my Mac are pending until the patches are applied.
- Inspect `/api/education/`: the fields remain public Education data, with no account records or `starred_by` relationship.

The relevant extras beyond the required role/star behavior are the personal starred filter, public detail navigation, filter-preserving feedback, visible access explanations, accessible toggle state, and aggregate query optimization. A high rubric score still depends on correct local behavior, timely submission, accurate documentation, and explaining the code; passing automated tests does not guarantee a grade.

## Tutorial 5: JavaScript, AJAX, and Safe Rendering

This implementation follows [Tutorial 5](https://pbp.cs.ui.ac.id/en/tutorial/tutorial-5.html), using the supplied September 29 PDF and the current Assignment 4 commit as its base. The instructions explicitly allow adapting the example to existing fields and design. No schema change, fixture reload, new framework, or build step is needed.

| Tutorial requirement | Portfolio implementation |
| --- | --- |
| Reusable notifications | `components/toast.html` in the shared base and `toast.js`; manual popover, success/error styling, dismissal, replacement timers, and textContent |
| Fetch project JSON | `show_projects` renders the shell and an unbound ProjectForm; JavaScript fetches `/api/projects/` and creates the cards |
| Include stars | Custom JsonResponse includes `star_count`, `is_starred`, and `starred_by_names`; the relation is prefetched |
| Live title search | Trimmed `title` parameter, `icontains`, 300 ms debounce, AbortController, and a generation check for late responses |
| Add-project popover | Owner-only form using all existing editable fields; native Cancel, Escape, and outside-click dismissal |
| Create without a page reload | POST `/projects/add-ajax/` with FormData and a CSRF header; validate ProjectForm, return JSON, reset on success, refresh the current search |
| Validation and access errors | JSON 400 with field errors, JSON 403 for unauthorized accounts, inline messages, and error toast; failed submissions retain input |
| XSS protection | Escape every dynamic card value; use textContent for errors/toasts; strip tags from new form text and reject required values that become empty |

The Project JSON keeps `model`, `pk`, and `fields` for compatibility and adds local action URLs generated with Django `reverse()`. Its computed fields make it a display API, not a document to pass back into Django's model deserializer. The view no longer deserializes Project JSON. Education and Experience retain their existing flow. Project XML remains available through Django's serializer and does not contain the new computed star fields.

The current model uses `summary`, `contribution`, and `technologies` in place of the tutorial example's `description` and `tech_stack`. Organization, project context, award, featured styling, and display order are preserved. The existing model has no image or external project URL field, so none is invented for this tutorial.

`escapeHtml` handles ampersands, angle brackets, and both kinds of quotation mark. The renderer also checks that action URLs are local paths: escaping HTML alone would not block a `javascript:` URL. `ProjectForm.clean()` calls `super().clean()`, then applies `strip_tags().strip()` to editable text fields and attaches field-specific validation errors. Both creation endpoints share it. Stripping tags is an extra data-cleaning step, not a guarantee of HTML safety: old/imported content must still be escaped, and text such as `List<String>` loses its tag-shaped portion. No intentionally unsafe XSS demo is left in the application.

Authorization remains server-side. Ordinary members, staff-only accounts, and Education Editors cannot add projects, even by posting directly to the AJAX endpoint. The endpoint deliberately returns JSON 403 instead of redirecting to a login page. CSRF middleware remains enabled; a middleware rejection can be HTML, which the client handles as an error. The client disables repeated submission while saving and does not automatically retry an uncertain network failure.

The interface keeps the featured dark card, tags, expandable contributions, and responsive grid. Loading, no data, no matches, and request failure have distinct states. Search also supports Enter, a Search button, Clear, a retained query value, and a matching URL. A successful addition refreshes the active search; a new project that does not match that search will remain filtered out. The original `/projects/add/` page remains usable; the dynamic project list requires JavaScript. Native popovers are used in current Brave/Chromium and other browsers with Popover API support.

### Local verification after applying Tutorial 5

1. Run `python manage.py check`, `python manage.py test`, `python manage.py makemigrations --check --dry-run`, and `git diff --check`. Optionally run the Node test command above.
2. As a visitor, open Projects. Confirm the real cards load, contribution sections expand, and detail links work. Search mixed-case titles, type quickly, clear the query, and try a title that matches nothing.
3. As the owner, open Add project. Check all fields, Cancel/Escape, and the scrollable form at desktop and approximately 390 px width. Create only a temporary test record; confirm the popover closes, a success toast appears, and the matching card arrives without a page reload.
4. Try a temporary title containing only `<img src=x onerror="alert(1)">`. The form must reject it, retain the input, show a title error and an error toast, and execute no JavaScript. Cancel afterwards.
5. Check star/unstar and owner deletion (cancel once, then delete the temporary record). Check the member/Editor/owner Education permissions and original account navigation.
6. In browser developer tools, temporarily block the Project API request to exercise the error state. Unblock it and use Try again. Stop only the development server to simulate a lost connection while adding, and check the list before retrying to avoid an accidental duplicate.

Tutorial 5's PDF states a deadline of **Wednesday, September 30, 2026** and requires a public GitHub **commit URL** showing the final result, pushed before the deadline. This README records implementation and preparation tests, not submission or deployment. Local verification, commit, push, and SCELE submission are still to be completed for Tutorial 5.

## AI Usage Disclosure

I used **ChatGPT** for explanations, implementation suggestions, fixtures, tests etc.
| Stage | Assistance requested | Review or limitation |
| --- | --- | --- |
| Earlier assignments | Help with the responsive portfolio, models, and template structure | I supplied the real portfolio content, tested locally, and reported layout and data issues. |
| Earlier debugging | Help with stale CSS and example tutorial data | A hard refresh resolved the browser cache issue; the copied example experience was replaced with my own content. |
| Tutorial 3 | Adapt project forms and JSON/XML delivery to the existing Project model | The implementation reused my actual model fields; the previous README records 28 passing local tests. |
| Assignment 3 planning | Implement the official assignment in one compatible patch | Education was chosen as an additional section, with year-based fields to avoid inventing exact study dates. |
| Assignment 3 code | Create/update/delete forms, JSON delivery, shared templates, and validation | The patch was based on the exact GitHub commit `ce1d5855ee719b5682ef8202455835003237b360`; static checks and patch-application checks were used during preparation. |
| Assignment 3 verification | Add tests for the new behavior and document the data flow | 22 tests were added. Django could not be installed in the patch preparation environment. I subsequently ran the test suite and browser checks successfully on my Mac and reported the result. |
| Tutorial 4 | Adapt the official tutorial to the latest GitHub version as a patch | ChatGPT/Codex read the tutorial, inspected commit `8d78e2572819b5536f015672dc431a02b015bbd5`, generated the implementation and tests, and ran automated checks in a separate environment. My Mac and browser verification is not claimed by those checks. |
| Assignment 4 | Continue on top of Tutorial 4 and review the appearance | ChatGPT/Codex generated the roles/stars implementation, tests and README. I subsequently applied and pushed it and reported that the appearance was correct. |
| Tutorial 5 | Adapt the uploaded tutorial PDF to my latest code and provide a patch | ChatGPT/Codex implemented JavaScript, AJAX, validation, tests and documentation against commit `a6ee42a217d1301ce1e8dff277f84bd1c4725b7b`. The separate preparation run passed 105 Django tests and 13 JavaScript tests; I still need to apply the patch and verify the browser behavior locally. |

AI assistance can produce code that looks plausible without proving that it runs. Static syntax checks cannot establish database migration compatibility, successful requests, or mobile usability. I therefore checked locally rather than treating its static checks as a runtime result. Understanding the update, CSRF, and JSON flow remains my responsibility when explaining the implementation.

The documentation distinguishes AI preparation from my local verification. The final verification status was updated after I reported that the local checks worked. Earlier manual debugging, such as resolving stale CSS and removing example records, illustrates why generated suggestions require practical review.

### Further Development

Possible next steps include project editing, an edit history for owner/editor changes, and reproducible dependency versions. Skills remain static. No audit trail, project update view, or new deployment is claimed by Assignment 4.
