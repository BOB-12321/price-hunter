// Price Hunter — mobile SPA
// Phase 2: tab bar (Home / Basket / Stores / Hunt) backed by the JSON API.
// No build step; one file, no framework, no router.  Each tab is a function
// that returns a DOM tree; the tab bar just swaps the root <main> contents.

(() => {
  const $app = document.getElementById("app");
  const $tabs = document.querySelectorAll(".tab");
  const $modal = document.getElementById("modal");
  const $modalTitle = document.getElementById("modal-title");
  const $modalBody = document.getElementById("modal-body");
  const $modalSave = document.getElementById("modal-save");
  const $toast = document.getElementById("toast");

  // ---- State --------------------------------------------------------

  const state = {
    products: [],
    stores: [],
    memberships: [],
    hunts: [],
    basket: null,
  };

  let activeTab = "home";
  let modalContext = null; // { save: () => Promise<void> }

  // ---- API helpers --------------------------------------------------

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
      ...opts,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || JSON.stringify(body);
      } catch (_) { /* keep statusText */ }
      throw new Error(`${res.status} ${detail}`);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  const get  = (p) => api(p);
  const post = (p, body) => api(p, { method: "POST", body: JSON.stringify(body) });
  const patch = (p, body) => api(p, { method: "PATCH", body: JSON.stringify(body) });
  const del  = (p) => api(p, { method: "DELETE" });

  async function refresh() {
    const [basket, products, stores, memberships, hunts] = await Promise.all([
      get("/api/basket"),
      get("/api/products"),
      get("/api/stores"),
      get("/api/memberships"),
      get("/api/hunts?limit=10"),
    ]);
    state.basket = basket;
    state.products = products;
    state.stores = stores;
    state.memberships = memberships;
    state.hunts = hunts;
  }

  // ---- Toast / modal ------------------------------------------------

  let toastTimer = null;
  function toast(msg, kind = "ok") {
    $toast.textContent = msg;
    $toast.className = `toast toast-${kind}`;
    $toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { $toast.hidden = true; }, 2400);
  }

  function openModal({ title, body, save }) {
    $modalTitle.textContent = title;
    $modalBody.replaceChildren(...(Array.isArray(body) ? body : [body]));
    modalContext = { save };
    $modal.hidden = false;
  }
  function closeModal() {
    $modal.hidden = true;
    $modalBody.replaceChildren();
    modalContext = null;
  }
  $modal.addEventListener("click", (e) => {
    if (e.target.matches("[data-close]")) closeModal();
  });
  $modalSave.addEventListener("click", async () => {
    if (!modalContext) return;
    $modalSave.disabled = true;
    try {
      await modalContext.save();
      closeModal();
    } catch (err) {
      toast(err.message, "error");
    } finally {
      $modalSave.disabled = false;
    }
  });

  // ---- DOM helpers --------------------------------------------------

  function h(tag, attrs = {}, ...children) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") el.className = v;
      else if (k === "html") el.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") {
        el.addEventListener(k.slice(2).toLowerCase(), v);
      } else if (k === "data") {
        for (const [dk, dv] of Object.entries(v)) el.dataset[dk] = dv;
      } else if (v !== null && v !== undefined && v !== false) {
        el.setAttribute(k, v);
      }
    }
    for (const c of children.flat()) {
      if (c == null || c === false) continue;
      el.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return el;
  }

  // ---- Tabs ---------------------------------------------------------

  $tabs.forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  async function switchTab(name) {
    activeTab = name;
    $tabs.forEach((b) => {
      const on = b.dataset.tab === name;
      b.classList.toggle("is-active", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
    });
    await render();
  }

  async function render() {
    try {
      await refresh();
    } catch (err) {
      $app.replaceChildren(h("div", { class: "card" },
        h("h2", {}, "Service error"),
        h("p", { class: "meta" }, err.message),
      ));
      return;
    }
    if (activeTab === "home")   return renderHome();
    if (activeTab === "basket") return renderBasket();
    if (activeTab === "stores") return renderStores();
    if (activeTab === "hunt")   return renderHunt();
  }

  // ---- Home ---------------------------------------------------------

  function renderHome() {
    const productCount = state.products.length;
    const storeCount = state.stores.length;
    const membershipCount = state.memberships.length;
    const huntCount = state.hunts.length;
    const lastHunt = state.hunts[0];

    const phaseItems = [
      ["Phase 1", "Skeleton", true],
      ["Phase 2", "Basket · Stores · Memberships", true],
      ["Phase 3", "Tesco IE price pulls", false],
      ["Phase 4", "Dunnes, Lidl, Boots, SuperValu, Aldi", false],
      ["Phase 5", "Brand vs own-brand (Open Food Facts)", false],
      ["Phase 6", "Receipt OCR", false],
      ["Phase 7", "Watchlist + daily digest", false],
    ];

    $app.replaceChildren(
      h("section", { class: "card" },
        h("h2", {}, "Overview"),
        h("div", { class: "stats" },
          h("div", { class: "stat" },
            h("div", { class: "stat-value" }, String(productCount)),
            h("div", { class: "stat-label" }, "Products"),
          ),
          h("div", { class: "stat" },
            h("div", { class: "stat-value" }, String(storeCount)),
            h("div", { class: "stat-label" }, "Stores"),
          ),
          h("div", { class: "stat" },
            h("div", { class: "stat-value" }, String(membershipCount)),
            h("div", { class: "stat-label" }, "Cards"),
          ),
        ),
      ),

      h("section", { class: "card" },
        h("h2", {}, "Last hunt"),
        lastHunt
          ? h("div", { class: "hunt-result" },
              h("h4", {}, `Hunt #${lastHunt.id} · ${lastHunt.status}`),
              h("p", { class: "meta" },
                `${lastHunt.product_ids.length} products × ${lastHunt.store_ids.length} stores · ${formatDate(lastHunt.created_at)}`,
              ),
            )
          : h("p", { class: "empty" }, "No hunts yet — set up your basket and stores first."),
      ),

      h("section", { class: "card" },
        h("h2", {}, "Roadmap"),
        h("ul", { class: "phase-list" },
          ...phaseItems.map(([tag, name, done]) =>
            h("li", {},
              h("span", { class: "phase" }, tag),
              name,
              done
                ? h("span", { class: "done" }, "✓")
                : h("span", { class: "now" }, "next"),
            ),
          ),
        ),
      ),

      h("p", { class: "meta", style: "text-align:center;margin-top:8px" },
        `v${state.basket ? "0.2.0" : "0.1.0"} · Tailscale-only · 100.105.66.115:3016`,
      ),
    );
  }

  // ---- Basket -------------------------------------------------------

  function renderBasket() {
    const items = state.products;
    const list = items.length
      ? h("ul", { class: "list" },
          ...items.map((p) => basketItemRow(p)),
        )
      : h("p", { class: "empty" }, "Your basket is empty. Add a product to get started.");

    $app.replaceChildren(
      h("section", { class: "card" },
        h("div", { class: "row" },
          h("h2", { style: "flex:1;margin:0" }, `Basket (${items.length})`),
          h("button", { class: "btn btn-primary btn-small", onClick: openAddProductModal },
            "+ Add product",
          ),
        ),
      ),
      list,
    );
  }

  function basketItemRow(p) {
    return h("li", { class: "list-item" },
      h("div", { style: "flex:1" },
        h("div", { class: "name" }, p.name),
        h("div", { class: "sub" },
          [p.brand, p.size, p.category].filter(Boolean).join(" · ") || "—",
        ),
      ),
      h("div", { class: "actions" },
        h("button", { class: "icon-btn", title: "Edit",
          onClick: () => openEditProductModal(p) }, "✎"),
        h("button", { class: "icon-btn", title: "Delete",
          onClick: () => deleteProduct(p) }, "🗑"),
      ),
    );
  }

  function openAddProductModal() {
    openProductModal(null);
  }
  function openEditProductModal(p) {
    openProductModal(p);
  }
  function openProductModal(existing) {
    const isEdit = !!existing;
    const fields = {
      name:    field("Name", existing?.name || "", { required: true, autofocus: true }),
      brand:   field("Brand", existing?.brand || ""),
      size:    field("Size (e.g. 250g, 1L)", existing?.size || ""),
      category: field("Category", existing?.category || "", { placeholder: "Dairy, Bakery, Cleaning…" }),
      barcode: field("Barcode (optional)", existing?.barcode || ""),
      notes:   textarea("Notes", existing?.notes || ""),
    };
    const body = [
      h("div", { class: "field" }, fields.name.labelEl, fields.name.input),
      h("div", { class: "field-row" },
        h("div", { class: "field" }, fields.brand.labelEl, fields.brand.input),
        h("div", { class: "field" }, fields.size.labelEl, fields.size.input),
      ),
      h("div", { class: "field-row" },
        h("div", { class: "field" }, fields.category.labelEl, fields.category.input),
        h("div", { class: "field" }, fields.barcode.labelEl, fields.barcode.input),
      ),
      h("div", { class: "field" }, fields.notes.labelEl, fields.notes.input),
    ];
    openModal({
      title: isEdit ? "Edit product" : "Add product",
      body,
      save: async () => {
        const payload = collectProductPayload(fields);
        if (!payload.name) throw new Error("Name is required");
        if (isEdit) {
          await patch(`/api/products/${existing.id}`, payload);
          toast("Product updated");
        } else {
          await post("/api/products", payload);
          toast("Product added");
        }
        await render();
      },
    });
  }

  function collectProductPayload(fields) {
    return {
      name:     fields.name.input.value.trim(),
      brand:    fields.brand.input.value.trim() || null,
      size:     fields.size.input.value.trim() || null,
      category: fields.category.input.value.trim() || null,
      barcode:  fields.barcode.input.value.trim() || null,
      notes:    fields.notes.input.value.trim() || null,
    };
  }

  async function deleteProduct(p) {
    if (!confirm(`Delete "${p.name}"?`)) return;
    await del(`/api/products/${p.id}`);
    toast("Product deleted");
    await render();
  }

  // ---- Stores -------------------------------------------------------

  function renderStores() {
    const list = state.stores.length
      ? h("ul", { class: "list" },
          ...state.stores.map((s) => storeRow(s)),
        )
      : h("p", { class: "empty" }, "No stores yet. Add one or run the seed script.");

    $app.replaceChildren(
      h("section", { class: "card" },
        h("div", { class: "row" },
          h("h2", { style: "flex:1;margin:0" }, `Stores (${state.stores.length})`),
          h("button", { class: "btn btn-primary btn-small",
            onClick: openAddStoreModal }, "+ Add store"),
        ),
        state.memberships.length
          ? h("div", { class: "chips", style: "margin-top:10px" },
              ...state.memberships.map((m) => {
                const s = state.stores.find((x) => x.id === m.store_id);
                const todo = (m.account_label || "").toLowerCase().includes("todo");
                return h("span", { class: `chip ${todo ? "chip-warn" : "chip-ok"}` },
                  `${s ? s.name : "?"} · ${m.programme}`,
                );
              }),
            )
          : null,
      ),
      list,
    );
  }

  function storeRow(s) {
    const ms = state.memberships.filter((m) => m.store_id === s.id);
    return h("li", { class: "list-item" },
      h("div", { style: "flex:1" },
        h("div", { class: "name" },
          s.name,
          ...ms.map((m) =>
            h("span", { class: "mb", style: "margin-left:8px" }, m.programme),
          ),
        ),
        h("div", { class: "sub" },
          [s.kind, s.location_label].filter(Boolean).join(" · ") || "—",
        ),
      ),
      h("div", { class: "actions" },
        h("button", { class: "icon-btn", title: "Add membership",
          onClick: () => openAddMembershipModal(s) }, "🏷"),
        h("button", { class: "icon-btn", title: "Delete",
          onClick: () => deleteStore(s) }, "🗑"),
      ),
    );
  }

  function openAddStoreModal() {
    const fields = {
      name: field("Store name", "", { required: true, autofocus: true }),
      kind: selectField("Kind", {
        in_store: "In store",
        online: "Online only",
        both: "In store + online",
        manual: "Manual entry only",
      }, "in_store"),
      location: field("Location label", "Dublin Northside"),
      online_url: field("Online URL (optional)", ""),
    };
    const body = [
      h("div", { class: "field" }, fields.name.labelEl, fields.name.input),
      h("div", { class: "field" }, fields.kind.labelEl, fields.kind.input),
      h("div", { class: "field" }, fields.location.labelEl, fields.location.input),
      h("div", { class: "field" }, fields.online_url.labelEl, fields.online_url.input),
    ];
    openModal({
      title: "Add store",
      body,
      save: async () => {
        const name = fields.name.input.value.trim();
        if (!name) throw new Error("Name is required");
        await post("/api/stores", {
          name,
          kind: fields.kind.input.value,
          location_label: fields.location.input.value.trim() || null,
          online_url: fields.online_url.input.value.trim() || null,
        });
        toast("Store added");
        await render();
      },
    });
  }

  function openAddMembershipModal(store) {
    const fields = {
      programme: field("Programme", "", {
        required: true, autofocus: true,
        placeholder: "e.g. Clubcard, Real Rewards, Value Club…",
      }),
      account_label: field("Account label (optional)", ""),
    };
    openModal({
      title: `Add membership · ${store.name}`,
      body: [
        h("div", { class: "field" }, fields.programme.labelEl, fields.programme.input),
        h("div", { class: "field" }, fields.account_label.labelEl, fields.account_label.input),
      ],
      save: async () => {
        const programme = fields.programme.input.value.trim();
        if (!programme) throw new Error("Programme is required");
        await post("/api/memberships", {
          store_id: store.id,
          programme,
          account_label: fields.account_label.input.value.trim() || null,
        });
        toast("Membership added");
        await render();
      },
    });
  }

  async function deleteStore(s) {
    if (!confirm(`Delete "${s.name}"?`)) return;
    await del(`/api/stores/${s.id}`);
    toast("Store deleted");
    await render();
  }

  // ---- Hunt ---------------------------------------------------------

  function renderHunt() {
    const productOptions = state.products.map((p) => ({ value: p.id, label: p.name }));
    const storeOptions = state.stores.map((s) => ({ value: s.id, label: s.name }));
    const productSel = multiSelect("Products", productOptions);
    const storeSel = multiSelect("Stores", storeOptions);
    const canHunt = state.products.length > 0 && state.stores.length > 0;

    $app.replaceChildren(
      h("section", { class: "card" },
        h("h2", {}, "Start a price hunt"),
        h("p", { class: "meta" },
          canHunt
            ? "Pick products and stores, then start a hunt. Phase 3 will pull real prices."
            : "Add at least one product and one store before starting a hunt.",
        ),
        h("div", { class: "field", style: "margin-top:12px" },
          productSel.labelEl,
          productSel.input,
        ),
        h("div", { class: "field" },
          storeSel.labelEl,
          storeSel.input,
        ),
        h("button", {
          class: "btn btn-primary btn-block",
          style: "margin-top:6px",
          disabled: !canHunt,
          onClick: () => startHunt(productSel, storeSel),
        }, "🎯  Start hunt"),
      ),
      h("section", { class: "card" },
        h("h2", {}, `Recent hunts (${state.hunts.length})`),
        state.hunts.length
          ? h("ul", { class: "list" },
              ...state.hunts.map((hunt) =>
                h("li", { class: "list-item" },
                  h("div", { style: "flex:1" },
                    h("div", { class: "name" }, `Hunt #${hunt.id} · ${hunt.status}`),
                    h("div", { class: "sub" },
                      `${hunt.product_ids.length} products × ${hunt.store_ids.length} stores · ${formatDate(hunt.created_at)}`,
                    ),
                  ),
                ),
              ),
            )
          : h("p", { class: "empty" }, "No hunts yet."),
      ),
    );
  }

  async function startHunt(productSel, storeSel) {
    const product_ids = [...productSel.input.querySelectorAll("input:checked")].map((i) => +i.value);
    const store_ids   = [...storeSel.input.querySelectorAll("input:checked")].map((i) => +i.value);
    if (product_ids.length === 0) throw new Error("Pick at least one product");
    if (store_ids.length === 0)   throw new Error("Pick at least one store");
    await post("/api/hunts", { product_ids, store_ids });
    toast("Hunt queued");
    await render();
  }

  // ---- Form helpers -------------------------------------------------

  function field(label, value = "", opts = {}) {
    const id = "f_" + Math.random().toString(36).slice(2, 8);
    const input = h("input", {
      id, type: "text", value,
      placeholder: opts.placeholder || "",
      autocomplete: "off",
    });
    if (opts.required) input.required = true;
    if (opts.autofocus) setTimeout(() => input.focus(), 30);
    const labelEl = h("label", { for: id }, label);
    return { input, labelEl };
  }
  function textarea(label, value = "") {
    const id = "t_" + Math.random().toString(36).slice(2, 8);
    const input = h("textarea", { id, rows: 3 }, value);
    const labelEl = h("label", { for: id }, label);
    return { input, labelEl };
  }
  function selectField(label, options, selected) {
    const id = "s_" + Math.random().toString(36).slice(2, 8);
    const input = h("select", { id },
      ...Object.entries(options).map(([k, v]) =>
        h("option", { value: k, selected: k === selected }, v),
      ),
    );
    const labelEl = h("label", { for: id }, label);
    return { input, labelEl };
  }
  function multiSelect(label, options) {
    const id = "m_" + Math.random().toString(36).slice(2, 8);
    const all = options.length;
    const input = h("div", {
      id, class: "list",
      style: "max-height:200px;overflow-y:auto;padding:6px;background:var(--surface-2);border:1px solid var(--border);border-radius:var(--radius-sm)",
    },
      ...options.map((opt) =>
        h("label", { class: "list-item", style: "min-height:36px;background:transparent" },
          h("input", { type: "checkbox", value: opt.value, style: "margin-right:8px" }),
          opt.label,
        ),
      ),
    );
    if (options.length === 0) {
      input.appendChild(h("p", { class: "empty", style: "padding:6px" }, "Nothing to pick from yet."));
    }
    const labelEl = h("label", {}, label);
    return { input, labelEl, all };
  }

  function formatDate(iso) {
    try {
      const d = new Date(iso);
      return d.toLocaleString();
    } catch (_) { return iso; }
  }

  // ---- Boot ---------------------------------------------------------

  render().catch((err) => {
    $app.replaceChildren(
      h("div", { class: "card" },
        h("h2", {}, "Boot error"),
        h("p", { class: "meta" }, err.message),
      ),
    );
  });
})();
