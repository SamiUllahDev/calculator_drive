// Schema email
!function(){try{var s=document.getElementById('org-schema');if(s){var d=JSON.parse(s.textContent);d['@graph'][0]['email']='support'+'@'+'calculatordrive.com';s.textContent=JSON.stringify(d);}}catch(e){}}();

// Transitions
(function(){
  var pending = 2; // Wait for both styles.css and site.min.css
  function done() {
    if (--pending <= 0) {
      // Wait 2 frames: 1st frame to apply CSS, 2nd frame to paint without transitions
      requestAnimationFrame(function() {
        requestAnimationFrame(function() {
          document.body.classList.remove('no-transitions');
        });
      });
    }
  }
  // Hook into the stylesheet onload events
  var sheets = document.querySelectorAll('link[rel="stylesheet"][media="print"]');
  sheets.forEach(function(s) {
    if (s.media === 'all') { done(); } // Already loaded
    else { var orig = s.onload; s.onload = function() { if (orig) orig.call(this); done(); }; }
  });
  // Fallback: enable transitions after 3s even if CSS load events don't fire
  setTimeout(function() { document.body.classList.remove('no-transitions'); }, 3000);
})();

// Header Scroll Effect
(function() {
  var header = document.getElementById('site-header');
  if (!header) return;
  var lastScroll = 0;
  window.addEventListener('scroll', function() {
    var y = window.scrollY || window.pageYOffset;
    if (y > 10) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
    lastScroll = y;
  }, {passive: true});
})();

/* ── Share Logic ── */
function getShareData() {
  const url = window.location.href;
  const title = document.title;
  const desc = document.querySelector('meta[name="description"]');
  const text = desc ? desc.getAttribute('content') : title;
  return { url, title, text };
}

function toggleSharePopup(forceState) {
  const popup = document.getElementById('sharePopup');
  const fab = document.getElementById('shareFab');
  const overlay = document.getElementById('shareOverlay');
  const show = forceState !== undefined ? forceState : !popup.classList.contains('active');

  popup.classList.toggle('active', show);
  fab.classList.toggle('active', show);
  overlay.classList.toggle('active', show);

  if (show) {
    const d = getShareData();
    const e = encodeURIComponent;
    document.getElementById('shareFacebook').href = `https://www.facebook.com/sharer/sharer.php?u=${e(d.url)}`;
    document.getElementById('shareTwitter').href = `https://twitter.com/intent/tweet?url=${e(d.url)}&text=${e(d.title)}`;
    document.getElementById('shareWhatsapp').href = `https://wa.me/?text=${e(d.title + ' ' + d.url)}`;
    document.getElementById('shareLinkedin').href = `https://www.linkedin.com/shareArticle?mini=true&url=${e(d.url)}&title=${e(d.title)}`;
    document.getElementById('sharePinterest').href = `https://pinterest.com/pin/create/button/?url=${e(d.url)}&description=${e(d.title)}`;
    document.getElementById('shareReddit').href = `https://www.reddit.com/submit?url=${e(d.url)}&title=${e(d.title)}`;
    document.getElementById('shareTelegram').href = `https://t.me/share/url?url=${e(d.url)}&text=${e(d.title)}`;
    document.getElementById('shareEmail').href = `mailto:?subject=${e(d.title)}&body=${e(d.text + '\n\n' + d.url)}`;
    document.getElementById('shareCopyInput').value = d.url;

    /* Show native share on supported devices */
    if (navigator.share) {
      document.getElementById('shareNative').style.display = '';
    }
  }
}

function copyShareLink() {
  const input = document.getElementById('shareCopyInput');
  const btn = document.getElementById('shareCopyBtn');
  navigator.clipboard.writeText(input.value).then(() => {
    btn.textContent = window.DJANGO_VARS.trans.copied;
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = window.DJANGO_VARS.trans.copy;
      btn.classList.remove('copied');
    }, 2000);
  }).catch(() => {
    input.select();
    document.execCommand('copy');
    btn.textContent = window.DJANGO_VARS.trans.copied;
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = window.DJANGO_VARS.trans.copy;
      btn.classList.remove('copied');
    }, 2000);
  });
}

function nativeShare() {
  const d = getShareData();
  navigator.share({ title: d.title, text: d.text, url: d.url }).catch(() => {});
  toggleSharePopup(false);
}

/* Close on Escape */
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') toggleSharePopup(false);
});

/* Share FAB: lock to viewport bottom-right (inline !important beats stray CSS/cache) */
(function pinShareFabBottomRight() {
  function apply() {
    var fab = document.getElementById('shareFab');
    if (!fab) return;
    var rtl = document.documentElement.getAttribute('dir') === 'rtl';
    var narrow = window.matchMedia('(max-width: 475px)').matches;
    var bottom = narrow ? '20px' : '24px';
    var side = narrow ? '16px' : '24px';
    fab.style.setProperty('position', 'fixed', 'important');
    fab.style.setProperty('top', 'auto', 'important');
    fab.style.setProperty('margin', '0', 'important');
    fab.style.setProperty('float', 'none', 'important');
    fab.style.setProperty('bottom', bottom, 'important');
    fab.style.setProperty('z-index', '56', 'important');
    if (rtl) {
      fab.style.setProperty('left', side, 'important');
      fab.style.setProperty('right', 'auto', 'important');
    } else {
      fab.style.setProperty('right', side, 'important');
      fab.style.setProperty('left', 'auto', 'important');
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply);
  } else {
    apply();
  }
  window.addEventListener('resize', apply, { passive: true });
})();

// Footer Email Link
!function(){var a='support',b='calculatordrive.com',e=a+'@'+b;var l=document.getElementById('footer-email-link');var t=document.getElementById('footer-email-text');if(l)l.href='mai'+'lto:'+e;if(t)t.textContent=e;}();

// === YIELD HELPER: breaks long tasks into chunks to reduce TBT ===
function yieldToMain() {
  return new Promise(function(resolve) {
    setTimeout(resolve, 0);
  });
}

// === PHASE 1: Critical interactivity (mobile menu) — runs immediately ===
(function() {
  var mobileMenuButton = document.querySelector('.mobile-menu-button');
  var mobileMenu = document.getElementById('mobile-menu');
  var mobileMenuOverlay = document.getElementById('mobile-menu-overlay');
  var mobileMenuClose = document.querySelector('.mobile-menu-close');
  if (!mobileMenu || !mobileMenuOverlay) return;
  
  function isMenuOpen() {
    return mobileMenu.classList.contains('active');
  }
  
  function openMobileMenu() {
    mobileMenu.classList.add('active');
    mobileMenuOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    if (mobileMenuButton) {
      mobileMenuButton.setAttribute('aria-expanded', 'true');
    }
  }
  
  function closeMobileMenu() {
    mobileMenu.classList.remove('active');
    mobileMenuOverlay.classList.remove('active');
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
    if (mobileMenuButton) {
      mobileMenuButton.setAttribute('aria-expanded', 'false');
    }
  }
  
  if (mobileMenuButton) {
    mobileMenuButton.addEventListener('click', function(e) {
      e.stopPropagation();
      if (isMenuOpen()) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    });
  }
  
  if (mobileMenuClose) {
    mobileMenuClose.addEventListener('click', function(e) {
      e.stopPropagation();
      closeMobileMenu();
    });
  }
  
  if (mobileMenuOverlay) {
    mobileMenuOverlay.addEventListener('click', function(e) {
      e.stopPropagation();
      closeMobileMenu();
    });
  }
  
  // Close menu when pressing Escape key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && isMenuOpen()) {
      closeMobileMenu();
    }
  });
  
  // Close menu when clicking on any link inside the mobile menu
  mobileMenu.addEventListener('click', function(event) {
    const clickedLink = event.target.closest('a');
    const clickedButton = event.target.closest('button');
    
    if (clickedButton && clickedButton.classList.contains('mobile-menu-close')) {
      return;
    }
    
    if (clickedLink && (clickedLink.classList.contains('mobile-menu-link') || clickedLink.closest('.mobile-menu-link'))) {
      closeMobileMenu();
    }
  });
})();

// === PHASE 2: Language selectors — deferred to idle to reduce TBT ===
function initLanguageSelectors() {
  // Header Language Selector
  (function() {
    'use strict';
    var langBtn = document.getElementById('language-selector-btn');
    var langDropdown = document.getElementById('language-dropdown');
    var langChevron = document.getElementById('language-chevron');
    var langForm = document.getElementById('language-form');
    if (!langBtn || !langDropdown || !langForm) return;

    function isDropdownOpen() { return langDropdown.classList.contains('show'); }
    function openDropdown() {
      langDropdown.classList.add('show');
      if (langChevron) langChevron.style.transform = 'rotate(180deg)';
      langBtn.setAttribute('aria-expanded', 'true');
    }
    function closeDropdown() {
      langDropdown.classList.remove('show');
      if (langChevron) langChevron.style.transform = '';
      langBtn.setAttribute('aria-expanded', 'false');
    }
    function submitLanguageForm(languageCode) {
      closeDropdown();
      var langInput = langForm.querySelector('input[name="language"]');
      if (!langInput) {
        langInput = document.createElement('input');
        langInput.type = 'hidden';
        langInput.name = 'language';
        langForm.appendChild(langInput);
      }
      langInput.value = languageCode;
      langForm.submit();
    }
    langBtn.addEventListener('click', function(e) {
      e.stopPropagation(); e.preventDefault();
      isDropdownOpen() ? closeDropdown() : openDropdown();
    });
    langForm.querySelectorAll('button[name="language"]').forEach(function(button) {
      button.type = 'button';
      button.addEventListener('click', function(e) {
        e.stopPropagation(); e.preventDefault();
        var code = this.value || this.getAttribute('value');
        if (code) submitLanguageForm(code);
      });
    });
    document.addEventListener('click', function(e) {
      if (langBtn.contains(e.target) || langDropdown.contains(e.target) || langForm.contains(e.target)) return;
      if (isDropdownOpen()) closeDropdown();
    });
  })();

  // Footer Language Selector
  (function() {
    'use strict';
    var btn = document.getElementById('footer-language-selector-btn');
    var dropdown = document.getElementById('footer-language-dropdown');
    var chevron = document.getElementById('footer-language-chevron');
    var form = document.getElementById('footer-language-form');
    if (!btn || !dropdown || !form) return;

    function isOpen() { return dropdown.classList.contains('show'); }
    function open() {
      dropdown.classList.add('show');
      if (chevron) chevron.style.transform = 'rotate(180deg)';
      btn.setAttribute('aria-expanded', 'true');
    }
    function close() {
      dropdown.classList.remove('show');
      if (chevron) chevron.style.transform = '';
      btn.setAttribute('aria-expanded', 'false');
    }
    function submit(code) {
      close();
      var input = form.querySelector('input[name="language"]');
      if (!input) {
        input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'language';
        form.appendChild(input);
      }
      input.value = code;
      form.submit();
    }
    btn.addEventListener('click', function(e) {
      e.stopPropagation(); e.preventDefault();
      isOpen() ? close() : open();
    });
    form.querySelectorAll('button[name="language"]').forEach(function(button) {
      button.type = 'button';
      button.addEventListener('click', function(e) {
        e.stopPropagation(); e.preventDefault();
        var code = this.value || this.getAttribute('value');
        if (code) submit(code);
      });
    });
    document.addEventListener('click', function(e) {
      if (btn.contains(e.target) || dropdown.contains(e.target) || form.contains(e.target)) return;
      if (isOpen()) close();
    });
  })();
}

// Defer language selectors to idle
if ('requestIdleCallback' in window) {
  requestIdleCallback(initLanguageSelectors, {timeout: 2000});
} else {
  setTimeout(initLanguageSelectors, 100);
}

// Notification System
function showNotification(message, type = 'info') {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll('.notification');
  existingNotifications.forEach(notification => notification.remove());
  
  const notification = document.createElement('div');
  notification.className = `notification fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white font-medium transform transition-all duration-300 translate-x-full`;
  
  // Set colors based on type
  switch(type) {
    case 'success':
      notification.classList.add('bg-green-600');
      break;
    case 'error':
      notification.classList.add('bg-red-600');
      break;
    case 'warning':
      notification.classList.add('bg-yellow-600');
      break;
    case 'info':
      notification.classList.add('bg-blue-600');
      break;
    default:
      notification.classList.add('bg-blue-600');
  }
  
  notification.textContent = message;
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => {
    notification.classList.remove('translate-x-full');
  }, 10);
  
  // Auto remove after 3 seconds
  setTimeout(() => {
    notification.classList.add('translate-x-full');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

// Favorite Calculator Functions - AJAX Implementation
function toggleFavorite(button, event) {
  if (!button) return;
  
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  const isOnFavoritesPage = window.location.pathname.includes('/favorites/');
  const icon = button.querySelector('.favorite-icon');
  if (!icon) {
    button.disabled = false;
    button.style.opacity = '1';
    button.style.cursor = 'pointer';
    return;
  }
  const wasFavorite = icon.classList.contains('fa-solid');
  const calculatorName = button.getAttribute('data-calculator-name');
  const calculatorUrl = button.getAttribute('data-calculator-url');
  const calculatorCategory = button.getAttribute('data-calculator-category') || '';
  const calculatorApp = button.getAttribute('data-calculator-app') || '';
  const calculatorDescription = button.getAttribute('data-calculator-description') || '';
  const isAuthenticated = button.getAttribute('data-is-authenticated') === 'true';
  
  if (!isAuthenticated) {
    const currentUrl = window.location.pathname + window.location.search;
    window.location.href = window.DJANGO_VARS.urls.login + '?next=' + encodeURIComponent(currentUrl);
    return;
  }
  
  button.disabled = true;
  button.style.opacity = '0.6';
  button.style.cursor = 'wait';
  
  const originalIconClasses = icon.className;
  const csrfToken = getCSRFToken();
  if (!csrfToken) {
    button.disabled = false;
    button.style.opacity = '1';
    button.style.cursor = 'pointer';
    showNotification(window.DJANGO_VARS.trans.securityTokenMissing, 'error');
    console.error('CSRF token not found');
    return;
  }
  
  fetch(window.DJANGO_VARS.urls.toggleFavorite, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
      'X-Requested-With': 'XMLHttpRequest',
      'Accept': 'application/json'
    },
    body: JSON.stringify({
      calculator_name: calculatorName,
      calculator_url: calculatorUrl,
      calculator_category: calculatorCategory,
      calculator_app: calculatorApp,
      calculator_description: calculatorDescription
    }),
    credentials: 'same-origin'
  })
  .then(response => {
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        const currentUrl = window.location.pathname + window.location.search;
        window.location.href = window.DJANGO_VARS.urls.login + '?next=' + encodeURIComponent(currentUrl);
        return;
      }
      return response.json().then(errData => {
        throw new Error(errData.error || `HTTP error! status: ${response.status}`);
      }).catch((e) => {
        if (e.message && !e.message.startsWith('HTTP error')) throw e;
        throw new Error(`HTTP error! status: ${response.status}`);
      });
    }
    return response.json();
  })
  .then(data => {
    if (!data) return;
    
    button.disabled = false;
    button.style.opacity = '1';
    button.style.cursor = 'pointer';
    
    if (data.success) {
      if (data.is_favorite) {
        icon.className = 'fa-solid fa-heart text-red-500 text-lg favorite-icon';
        button.setAttribute('aria-label', window.DJANGO_VARS.trans.removeFromFavorites);
        showNotification(window.DJANGO_VARS.trans.addSuccess, 'success');
      } else {
        icon.className = 'fa-regular fa-heart text-gray-400 text-lg favorite-icon';
        button.setAttribute('aria-label', window.DJANGO_VARS.trans.addToFavorites);
        
        if (isOnFavoritesPage && wasFavorite) {
          setTimeout(() => {
            const removedEvent = new CustomEvent('favoriteRemoved', {
              detail: { button: button },
              bubbles: true,
              cancelable: true
            });
            document.dispatchEvent(removedEvent);
          }, 100);
        }
        
        showNotification(window.DJANGO_VARS.trans.removeSuccess, 'info');
      }
    } else {
      const errorMsg = data.error || window.DJANGO_VARS.trans.errorOccurred;
      showNotification(errorMsg, 'error');
      console.error('Server Error:', data);
    }
  })
  .catch(error => {
    button.disabled = false;
    button.style.opacity = '1';
    button.style.cursor = 'pointer';
    icon.className = originalIconClasses;
    const errorMsg = error.message || window.DJANGO_VARS.trans.failedToUpdate;
    showNotification(errorMsg, 'error');
    console.error('AJAX Error Details:', {
      error: error.message,
      calculator: calculatorName,
      url: calculatorUrl
    });
  });
}

// Check favorite status on page load - uses bulk endpoint for efficiency
function checkFavorites() {
  const favoriteButtons = document.querySelectorAll('.favorite-btn');
  if (!favoriteButtons.length) return;
  
  const buttonMap = {};
  let hasAuthenticated = false;
  
  favoriteButtons.forEach(button => {
    const isAuthenticated = button.getAttribute('data-is-authenticated') === 'true';
    if (!isAuthenticated) return;
    
    const calculatorUrl = button.getAttribute('data-calculator-url');
    if (!calculatorUrl) return;
    
    const normalizedUrl = calculatorUrl.replace(/\/+$/, '');
    if (!buttonMap[normalizedUrl]) {
      buttonMap[normalizedUrl] = [];
    }
    buttonMap[normalizedUrl].push(button);
    hasAuthenticated = true;
  });
  
  if (!hasAuthenticated) return;
  
  const urls = Object.keys(buttonMap);
  if (!urls.length) return;
  
  const csrfToken = getCSRFToken();
  
  fetch(window.DJANGO_VARS.urls.checkFavoritesBulk, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
      'X-Requested-With': 'XMLHttpRequest',
      'Accept': 'application/json'
    },
    body: JSON.stringify({ calculator_urls: urls }),
    credentials: 'same-origin'
  })
  .then(response => {
    if (response.status === 401 || response.status === 403) {
      return null;
    }
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    if (!data || !data.success) return;
    
    const favorites = data.favorites || {};
    
    for (const [url, isFavorite] of Object.entries(favorites)) {
      const buttons = buttonMap[url] || [];
      buttons.forEach(button => {
        const icon = button.querySelector('.favorite-icon');
        if (!icon) return;
        
        if (isFavorite) {
          icon.className = 'fa-solid fa-heart text-red-500 text-lg favorite-icon';
          button.setAttribute('aria-label', window.DJANGO_VARS.trans.removeFromFavorites);
        } else {
          icon.className = 'fa-regular fa-heart text-gray-400 text-lg favorite-icon';
          button.setAttribute('aria-label', window.DJANGO_VARS.trans.addToFavorites);
        }
      });
    }
  })
  .catch(error => {
    console.error('Error checking favorites:', error);
  });
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function getCSRFToken() {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content');
  }
  return getCookie('csrftoken');
}

if ('requestIdleCallback' in window) {
  requestIdleCallback(function() { checkFavorites(); }, {timeout: 3000});
} else {
  setTimeout(function() { checkFavorites(); }, 200);
}

// Password Toggle Function
function togglePassword(inputId) {
  var input = document.getElementById(inputId);
  var button = input.nextElementSibling;
  var icon = button.querySelector('i');
  if (!icon) return;
  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.remove('fa-eye');
    icon.classList.add('fa-eye-slash');
  } else {
    input.type = 'password';
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }
}

// Deferred OG/Twitter/Keyword meta sync
window.addEventListener('load', function() {
  var t = document.title || '';
  var dm = document.querySelector('meta[name="description"]');
  var d = dm ? dm.getAttribute('content') : '';
  if (t && t !== 'Calculator Drive') {
    var ogT = document.querySelector('meta[property="og:title"]');
    if (ogT) ogT.setAttribute('content', t);
    var ogD = document.querySelector('meta[property="og:description"]');
    if (ogD && d) ogD.setAttribute('content', d);
    var twT = document.querySelector('meta[name="twitter:title"]');
    if (twT) twT.setAttribute('content', t);
    var twD = document.querySelector('meta[name="twitter:description"]');
    if (twD && d) twD.setAttribute('content', d);
  }
});
