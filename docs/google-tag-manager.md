# Google Tag Manager — installation

**Calculator Drive:** GTM is already loaded on every public page via `core/templates/core/base.html` (snippet in `<head>` and `noscript` immediately after `<body>`). Container ID: `GTM-53Q57649`.

Use the steps below when setting up a new property, verifying the install, or copying the official snippet.

## Install Google Tag Manager

Copy the code below and paste it onto every page of your website.

### 1. Paste this code as high in the `<head>` of the page as possible

```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-53Q57649');</script>
<!-- End Google Tag Manager -->
```

### 2. Paste this code immediately after the opening `<body>` tag

```html
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-53Q57649"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
```

## Changing the container ID

If you replace `GTM-53Q57649`, update both places in `core/templates/core/base.html` (the `<script>` block in `<head>` and the `noscript` iframe `src`).
