/*
 * ChillGo sticky mobile add-to-cart (Section 5.3).
 * Watches the main <product-form> (Dawn's buy-box) with an IntersectionObserver
 * and reveals the sticky bar once it scrolls out of view. Mobile only — the CSS
 * keeps .sticky-atc display:none above 749px, so we only toggle the inline style
 * below that width. Clicking the bar posts the current variant to /cart/add and
 * refreshes the cart drawer/bubble if the theme exposes one.
 */
(function () {
  'use strict';

  var MOBILE_QUERY = '(max-width: 749px)';

  function init() {
    var bar = document.querySelector('.sticky-atc');
    if (!bar) return;

    // Dawn wraps the main add-to-cart in <product-form>; fall back to the form.
    var buyBox =
      document.querySelector('product-form') ||
      document.querySelector('form[action$="/cart/add"]');
    if (!buyBox) return;

    var mq = window.matchMedia(MOBILE_QUERY);

    function show() {
      if (!mq.matches) return;
      bar.style.display = 'flex';
      bar.setAttribute('aria-hidden', 'false');
    }
    function hide() {
      bar.style.display = 'none';
      bar.setAttribute('aria-hidden', 'true');
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          // Buy box off-screen + we're on mobile => show the sticky bar.
          if (!entry.isIntersecting && mq.matches) {
            show();
          } else {
            hide();
          }
        });
      },
      { threshold: 0 }
    );
    observer.observe(buyBox);

    // Re-evaluate on breakpoint change (e.g. rotate to landscape / desktop).
    mq.addEventListener('change', function () {
      if (!mq.matches) hide();
    });

    // Keep the sticky price + variant id in sync when Dawn swaps variants.
    document.addEventListener('change', function (e) {
      if (!e.target.closest('variant-selects, .product-form__input')) return;
      syncVariant(buyBox, bar);
    });

    bar.querySelector('.sticky-atc__button').addEventListener('click', function () {
      addToCart(bar);
    });
  }

  function syncVariant(buyBox, bar) {
    var idInput = buyBox.querySelector('[name="id"]');
    var button = bar.querySelector('.sticky-atc__button');
    if (idInput && idInput.value) {
      button.setAttribute('data-variant-id', idInput.value);
    }
  }

  function addToCart(bar) {
    var button = bar.querySelector('.sticky-atc__button');
    var variantId = button.getAttribute('data-variant-id');
    if (!variantId || button.disabled) return;

    var original = button.textContent;
    button.disabled = true;
    button.textContent = 'Adding…';

    fetch('/cart/add.js', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ items: [{ id: Number(variantId), quantity: 1 }] })
    })
      .then(function (r) {
        if (!r.ok) throw new Error('cart/add failed');
        return r.json();
      })
      .then(function () {
        button.textContent = 'Added ✓';
        refreshCart();
        setTimeout(function () {
          button.textContent = original;
          button.disabled = false;
        }, 1500);
      })
      .catch(function () {
        button.textContent = original;
        button.disabled = false;
      });
  }

  // Ask Dawn's cart drawer/icon-bubble to re-render, if present.
  function refreshCart() {
    var cart =
      document.querySelector('cart-drawer') ||
      document.querySelector('cart-notification');
    if (cart && typeof cart.renderContents === 'function') {
      fetch(window.Shopify.routes.root + 'cart.js')
        .then(function (r) { return r.json(); })
        .then(function (state) { cart.renderContents({ sections: [], cart: state }); })
        .catch(function () {});
    } else {
      var drawer = document.querySelector('cart-drawer');
      if (drawer && typeof drawer.open === 'function') drawer.open();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
