# Marcel Mikula — Personal Portfolio

A responsive personal portfolio developed for Platform-Based Programming at the Faculty of Computer Science, Universitas Indonesia.

The project started as a static About Me page. Tutorial 2 introduced database-backed experience entries; Assignment 2 adds a project overview, individual project pages, and reusable page templates.

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
- Fourteen automated tests covering models, pages, navigation, empty states, and fixture reloading

The frontend uses HTML5, CSS3, and Django Template Language. It uses CSS Grid, Flexbox, CSS variables, and `clamp()`; no frontend framework or JavaScript library is required.

## Pages and Navigation

| Page or section | URL | Content |
| --- | --- | --- |
| Home | `/` | Profile, education, and Data & AI |
| Projects | `/projects/` | All project records from the database |
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
| `main/views.py` | Profile context and views for the home, experience, project list, and project detail pages |
| `main/urls.py` | Named routes in the `main` namespace |
| `main/tests.py` | Automated model, page, and fixture tests |
| `main/migrations/` | Versioned database schema changes |
| `main/fixtures/main/projects.json` | Three portfolio project records |
| `main/fixtures/main/experience.json` | The B. Braun experience record |
| `templates/base.html` | Shared document structure, navigation, footer, and content block |
| `templates/index.html` | Profile, education, and Data & AI content |
| `templates/projects.html` | Project list and empty state |
| `templates/project_detail.html` | Individual project content |
| `templates/experience.html` | Experience list and empty state |
| `static/css/style.css` | Shared styling and responsive rules |
| `static/img/Download.jpeg` | Profile photograph |
| `manage.py` | Django management commands |

## Local Setup

These instructions are for a fresh checkout of the Assignment 2 branch. Install Python 3.13 and Git first.

1. Clone the branch and enter the repository:

   ```bash
   git clone --branch feature/assignment_2_projects https://github.com/Marcelm1806/myportofolio.git
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

Projects and experience are rendered from database records. Profile values are supplied by the view, while education and skills remain in the home template. Content can currently be maintained through fixtures or the Django shell. A portfolio editing interface and project filters are possible future extensions.

## Testing and Verification

The last recorded local run completed **14 tests successfully**:

| Test group | Count | Coverage |
| --- | --- | --- |
| Tutorial 2 tests | 6 | Home and experience pages, navigation, missing page, model behavior, empty experience list, and completed status |
| Project list tests | 3 | Project content and template, empty state, and links from existing pages |
| Project detail tests | 3 | Selected project content, missing project ID, and detail links from the list |
| Project fixture test | 1 | Loading twice without duplicates while preserving an independently created project |
| Experience history test | 1 | Saving and displaying historical dates, organization, timeline, and responsibilities |

Run the full suite and development checks with:

```bash
python manage.py test
python manage.py makemigrations --check --dry-run
git diff --check
```

The recorded results were 14 passing tests, `No changes detected`, and no whitespace errors. The local test run also printed a warning about the missing collected `staticfiles/` directory; the test suite completed successfully.

Tests run against a separate test database. Example names used in test cases are test data. These checks exercise model behavior and rendered HTTP responses; they do not measure browser layout or verify the truth of portfolio claims.

For a manual browser check:

- Open the home, Projects, and Experience pages and follow each project detail link.
- Expand and collapse the contribution sections, and follow the return link from a detail page.
- Check desktop and narrow mobile widths, including approximately 390 pixels, for readable content and horizontal overflow.
- Use the keyboard to follow navigation and the skip link.
- Confirm that the three projects and the B. Braun responsibilities match the intended content.

## Weekly Progress

| Stage | Progress |
| --- | --- |
| Tutorial 0 | Created the repository, configured Git, prepared the virtual environment, and initialized Django. |
| Tutorial 1 | Built the About Me page with profile information, a photograph, and external links. |
| Assignment 1 | Added static projects, experience, education, and skills; implemented responsive styling and native interactive details. |
| Tutorial 2 | Introduced the `main` app, the `Experience` model, ORM-backed views, named URLs, migrations, and six tests. |
| Assignment 2 | Added the `Project` model and migration, project list and detail pages, shared templates, fixtures, and additional tests. Restored the B. Braun content as database records and extended experience fields. |

## Reflective Questions

The Assignment 1 answers below describe the static version submitted for that assignment. Later work introduced the database-backed features discussed under Assignment 2.

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

## AI Usage Disclosure

I used **ChatGPT** during Assignments 1 and 2. Assistance included explanations, substantial HTML/CSS and Python code suggestions, complete replacement templates, fixture content, tests, debugging, Git commands, and README drafting.



The code and documentation were developed with AI assistance. Thus for example the development of this specific README could easily facilitated. My contribution included selecting and checking the personal content, applying changes, running migrations and tests, inspecting the site, and reporting problems that required another iteration.

### Prompt Strategy and Assistance Log

I asked for changes in stages, using the existing portfolio as context. When an editing instruction was unclear, I requested the complete affected file. I then shared errors or test results before proceeding. The entries below summarize those requests; they are a paraphrased development log.

| Stage | Assistance requested | My action or observed result |
| --- | --- | --- |
| Assignment 1: layout | Suggest semantic HTML and responsive CSS for my portfolio. | Applied the code and inspected the profile, project cards, navigation, and expandable descriptions. |
| Assignment 1: mobile layout | Explain how to check the page in a mobile viewport. | Used Brave's iPhone 12 Pro emulation and checked wrapping and content order. |
| Assignment 1: CSS debugging | Explain why the design still looked unchanged. | Used a hard refresh; the updated stylesheet then appeared. |
| Tutorial 2: routing | Help resolve `NoReverseMatch` after changing the navigation. | Corrected links to registered routes and home-page anchors. |
| Tutorial 2: database content | Explain why both the tutorial example and my entry appeared. | Learned that another `create()` call adds a record, and removed the unwanted example through a filtered query. |
| Assignment 2: MVT | Extend the portfolio with database-backed projects and additional useful functionality. | Applied the model, migration, views, named routes, list page, and detail page. |
| Assignment 2: template inheritance | Provide the full `index.html` because the extraction into `base.html` was unclear. | Replaced the template and obtained a passing nine-test run at that stage. |
| Assignment 2: data and tests | Make the three projects reproducible and test the detail pages. | Loaded fixtures and added tests for selected records, missing IDs, links, and repeated imports. |
| Assignment 2: experience | Restore the B. Braun content from Assignment 1 on the database-backed page. | Applied the experience migration, loaded its fixture, removed the temporary tutorial entry, and obtained 14 passing tests. |
| Assignment 2: documentation | Explain the implementation and prepare setup instructions, reflections, and AI disclosure. | Supplied the actual terminal output and screenshot as evidence for the documentation draft. |

### Critical Reflection on AI Assistance

AI assistance made it easier to develop a consistent structure, but it did not remove the need to understand how the pieces fit together. The template-inheritance step was a concrete example: the initial editing instructions were unclear to me, so I asked for the complete file. The relevant distinction is that `base.html` provides the shared document structure and child templates fill its content block.

The database work exposed another limitation of copying instructions without understanding their effect. Repeating `Experience.objects.create()` produced another entry. For Assignment 2, fixed-ID fixtures and a repeated-import test gave me a more controlled way to load portfolio data.

I also had to distinguish the date a record is created from the date employment began. The tutorial's automatic timestamp was unsuitable for entering a historical start date through normal object creation. The revised model accepts an explicit date, and a test checks that it is retained and displayed.

Passing tests provide evidence for the behaviors they cover. They cannot establish whether a personal claim is accurate, whether the page looks good in every browser, or what grade the work will receive. I supplied and checked the personal information, used browser observations alongside the automated results, and treated AI grading estimates as suggestions rather than guarantees.

### Further Development

Useful next steps would be an editing interface for portfolio content, topic filters for projects, and database models for education and skills. Reproducible dependency versions would also make environment setup more predictable. These are possible future improvements rather than features claimed in the current implementation.
