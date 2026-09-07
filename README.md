# Marcel Mikula — Personal Portfolio

A responsive personal portfolio developed for the Platform-Based Programming course at the Faculty of Computer Science, Universitas Indonesia.

This repository extends the About Me page from Tutorial 1 with sections for selected projects, professional experience, education, and Data & AI topics.

[View the Assignment 1 specification](https://pbp.cs.ui.ac.id/en/assignments/individual/tugas-1.html)

## Student Information

* **Name:** Marcel Mikula
* **NPM:** 2606816592
* **Class:** PBP A

## Features

* Personal profile with biography, academic program, and external links
* Three selected project cards featuring Porsche, ING, and my bachelor's thesis
* Professional experience and education sections
* Data & AI topic overview
* Responsive layouts for desktop and mobile screens
* Native interactive project descriptions using HTML `<details>` and `<summary>`
* Keyboard focus states and a skip-to-content link for accessibility
* Hover effects, CSS Grid, Flexbox, CSS variables, and reduced-motion support

## Technologies

* Python
* Django
* HTML5
* CSS3
* WhiteNoise

No frontend framework or JavaScript library is used. The page is built with plain HTML5 and CSS3 as required for Assignment 1.

## Project Structure

```text
myportofolio/
├── portofolio/
│   ├── settings.py
│   ├── urls.py
│   └── views.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── img/
│       └── Download.jpeg
├── templates/
│   └── index.html
├── manage.py
├── requirements.txt
└── README.md
```

## Local Setup

1. Clone the repository and enter the project directory:

```bash
git clone https://github.com/Marcelm1806/myportofolio.git
cd myportofolio
```

2. Create and activate a virtual environment:

```bash
python -m venv env
source env/bin/activate
```

On Windows, activate it with:

```bash
env\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Apply the database migrations:

```bash
python manage.py migrate
```

5. Check the Django configuration:

```bash
python manage.py check
```

6. Start the development server:

```bash
python manage.py runserver
```

The portfolio can then be opened at `http://127.0.0.1:8000/`.

## Weekly Progress

| Stage        | Progress                                                                                                                                                              |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tutorial 0   | Created the repository, configured Git, prepared the virtual environment, and initialized the Django project.                                                         |
| Tutorial 1   | Built the first About Me page with personal information, a photograph, and external profile links.                                                                    |
| Assignment 1 | Added projects, professional experience, education, and skills; created responsive layouts and interactive project details; improved accessibility and documentation. |

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

## AI Usage Disclosure

I used **ChatGPT** as an assistance tool during Assignment 1. It supported  English-language refinement, HTML and CSS suggestions, debugging, and README review. Especially fancy designs like this setup guide or project structure can be done by chatgpt easily and facilitate project quality and readabiliy. All files were edited manually, and all Git commands and local tests were performed by me.

### Prompt and Assistance Log

| Stage                | Assistance requested                                                                  | My verification or adjustment                                                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HTML and CSS         | Asked for a semantic and responsive implementation using plain HTML5 and CSS3.        | Added the code manually, reviewed the semantic hierarchy, and tested the navigation, cards, links, and `<details>` elements locally.                                 |
| Responsive testing   | Asked how to test and improve the mobile layout.                                      | Tested the page using an iPhone 12 Pro viewport and checked wrapping, content order, readability, and horizontal overflow.                                           |
| Debugging            | Asked why the new CSS design was not initially visible.                               | Verified the static-file path and resolved the stale browser cache with a hard refresh.                                                                              |

### Critical Reflection on AI Assistance

AI-generated suggestions were useful for creating an initial structure, but they were not automatically reliable. The AI could not independently verify how the website behaved in my local browser. I therefore ran Django myself, inspected the page on desktop and mobile, opened the interactive project sections, checked ignored files, and resolved the browser-cache issue manually. This process showed me that AI output should be treated as a draft that requires factual review, technical testing, and personal judgment rather than as a finished solution. Nevertheless, we are now able to experience the powerful capabilities of modern LLMs, which are especially good for tasks like webdevelopment, which saves time, reduces errors and prevent energy draining bugfixing.
