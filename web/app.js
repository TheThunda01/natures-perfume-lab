/* Local, dependency-free explorer. All scientific values come from data.js. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const data = window.PERFUME_DATA;
  if (!data) {
    $("data-error").hidden = false;
    $("molecule-name").textContent = "Data unavailable";
    return;
  }
  const entries = (value) =>
    Array.isArray(value)
      ? value
      : Object.entries(value || {}).map(([id, item]) => ({ id, ...item }));
  const molecules = entries(data.chemistry?.molecules || data.molecules);
  const enzymes = entries(data.enzymes);
  const reactions = entries(data.chemistry?.reactions || data.reactions);
  const esc = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (char) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[char],
    );
  const safeURL = (value) => {
    try {
      const u = new URL(value, location.href);
      return ["https:", "http:"].includes(u.protocol) ? u.href : null;
    } catch {
      return null;
    }
  };
  const state = {
    molecule: null,
    atom: null,
    carbonMap: null,
    mode: "2d",
    rx: 0.31,
    ry: -0.44,
  };
  const knownRoles = {
    gpp: ["SHARED PRECURSOR", "Geranyl diphosphate"],
    limonene: ["CYCLIC PRODUCT", "A carbon ring"],
    linalool: ["ACYCLIC ALCOHOL", "An open carbon chain"],
  };
  function moleculeId(m) {
    return String(m.id || m.name || "")
      .toLowerCase()
      .replaceAll(" ", "-");
  }
  function atomsOf(m) {
    return m.atoms || m.conformer?.atoms || m.coordinates?.atoms || [];
  }
  function bondsOf(m) {
    return m.bonds || m.conformer?.bonds || [];
  }
  function atomIndex(a, i) {
    return Number(a.index ?? a.idx ?? i);
  }
  function symbol(a) {
    return a.symbol || a.element || (a.atomic_number === 6 ? "C" : "");
  }
  function xyz(a) {
    const p = a.position || a.coordinates || a.coords;
    return p ? (Array.isArray(p) ? p : [p.x, p.y, p.z]) : [a.x, a.y, a.z];
  }
  function has3D(m) {
    return (
      atomsOf(m).length > 0 &&
      atomsOf(m).every(
        (a) => xyz(a).length === 3 && xyz(a).every(Number.isFinite),
      ) &&
      bondsOf(m).length > 0
    );
  }
  function carbonAtoms(m) {
    return atomsOf(m)
      .map((a, i) => ({ ...a, index: atomIndex(a, i) }))
      .filter((a) => symbol(a) === "C")
      .sort((a, b) => Number(atomLabel(a)) - Number(atomLabel(b)));
  }
  function atomMap(a) {
    return a.map_number || a.map_num || a.atom_map || a.map || null;
  }
  function atomLabel(a) {
    return atomMap(a) || a.index + 1;
  }
  function sanitizeSVG(raw) {
    if (!raw || typeof raw !== "string" || !raw.includes("<svg")) return null;
    const doc = new DOMParser().parseFromString(raw, "image/svg+xml");
    const svg = doc.querySelector("svg");
    if (!svg || doc.querySelector("parsererror")) return null;
    svg
      .querySelectorAll("script,foreignObject,iframe,image,a")
      .forEach((el) => el.remove());
    for (const el of [svg, ...svg.querySelectorAll("*")])
      for (const attr of [...el.attributes])
        if (/^on/i.test(attr.name) || /href$/i.test(attr.name))
          el.removeAttribute(attr.name);
    svg.setAttribute("role", "img");
    svg.setAttribute(
      "aria-label",
      `${state.molecule.name} two-dimensional structure`,
    );
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    return svg;
  }
  function chooseMolecule(id, moveFocus = false) {
    const m = molecules.find((m) => moleculeId(m) === id);
    if (!m) return;
    const previousMap = state.carbonMap;
    state.molecule = m;
    state.atom = null;
    $("molecule-list")
      .querySelectorAll("button")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.id === id)),
      );
    $("molecule-name").textContent = m.name || id;
    $("molecule-role").textContent =
      m.role || knownRoles[id]?.[0] || "MOLECULAR STRUCTURE";
    const svg = sanitizeSVG(m.svg || m.svg_2d || m.structure_svg);
    $("structure-2d").replaceChildren();
    if (svg) $("structure-2d").appendChild(svg);
    else
      $("structure-2d").innerHTML =
        '<p class="unavailable">A 2D drawing is not available for this structure.</p>';
    const carbons = carbonAtoms(m);
    const facts = [
      m.formula || m.molecular_formula,
      (m.carbon_count ?? carbons.length)
        ? `${m.carbon_count ?? carbons.length} carbon atoms`
        : null,
      m.mass != null ? `${Number(m.mass).toFixed(2)} g/mol` : null,
    ].filter(Boolean);
    $("molecule-facts").innerHTML = facts
      .map((f) => `<span class="fact">${esc(f)}</span>`)
      .join("");
    $("representation-note").textContent = m.representation || "";
    $("atom-buttons").innerHTML = carbons
      .map(
        (a) =>
          `<button type="button" class="atom-button" aria-pressed="false" data-atom="${a.index}" aria-label="Select carbon atom ${esc(atomLabel(a))}">C${esc(atomLabel(a))}</button>`,
      )
      .join("");
    $("atom-buttons")
      .querySelectorAll("button")
      .forEach((b) =>
        b.addEventListener("click", () => selectAtom(Number(b.dataset.atom))),
      );
    const mapped = carbons.length && carbons.every((a) => atomMap(a));
    const numbering = data.chemistry?.numbering;
    $("atom-label-note").textContent =
      mapped && numbering
        ? "Choose a carbon, then switch molecules to follow its declared lineage label."
        : mapped && data.chemistry?.atom_mapping_note
          ? data.chemistry.atom_mapping_note
          : "Atom labels refer to the selected structure; they do not establish a reaction mechanism.";
    $("mapping-details").hidden = !numbering;
    if (numbering)
      $("mapping-description").innerHTML = Object.values(numbering)
        .map((note) => `<p>${esc(note)}</p>`)
        .join("");
    $("view-3d").disabled = !has3D(m);
    $("view-3d").title = has3D(m)
      ? ""
      : "No generated conformer is available for this molecule.";
    if (!has3D(m)) state.mode = "2d";
    setMode(state.mode);
    const nextAtom =
      previousMap == null
        ? null
        : carbons.find((a) => atomMap(a) === previousMap);
    selectAtom(nextAtom?.index ?? null);
    if (moveFocus) {
      $("explorer").scrollIntoView({
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
      });
      $("molecule-list")
        .querySelector(`[data-id="${CSS.escape(id)}"]`)
        ?.focus({ preventScroll: true });
    }
  }
  function selectAtom(index) {
    state.atom = index;
    const carbons = carbonAtoms(state.molecule),
      selected = carbons.find((a) => a.index === index);
    state.carbonMap = selected ? atomMap(selected) : null;
    $("atom-buttons")
      .querySelectorAll("button")
      .forEach((b) =>
        b.setAttribute(
          "aria-pressed",
          String(Number(b.dataset.atom) === index),
        ),
      );
    $("atom-status").textContent = selected
      ? `Carbon ${atomLabel(selected)} selected in ${state.molecule.name}.`
      : "Choose a carbon atom to highlight it.";
    const svg = $("structure-2d").querySelector("svg");
    if (svg) {
      svg
        .querySelectorAll(".highlight-atom,.atom-halo")
        .forEach((el) =>
          el.classList.contains("atom-halo")
            ? el.remove()
            : el.classList.remove("highlight-atom"),
        );
      if (selected) {
        const targets = svg.querySelectorAll(`.atom-${index}`);
        targets.forEach((el) => el.classList.add("highlight-atom"));
        const point =
          selected.svg_position || selected.position_2d || selected.svg_coords;
        if (point) {
          const c = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "circle",
          );
          c.setAttribute("cx", point.x ?? point[0]);
          c.setAttribute("cy", point.y ?? point[1]);
          c.setAttribute("r", "11");
          c.setAttribute("class", "atom-halo");
          svg.appendChild(c);
        }
      }
    }
    draw3D();
  }
  function setMode(mode) {
    state.mode = mode === "3d" && has3D(state.molecule) ? "3d" : "2d";
    const is3 = state.mode === "3d";
    $("structure-2d").hidden = is3;
    $("structure-3d").hidden = !is3;
    $("rotation-controls").hidden = !is3;
    $("model-note").hidden = !is3;
    $("view-2d").setAttribute("aria-pressed", String(!is3));
    $("view-3d").setAttribute("aria-pressed", String(is3));
    if (is3) requestAnimationFrame(draw3D);
  }
  function draw3D() {
    if (!state.molecule || state.mode !== "3d") return;
    const canvas = $("molecule-canvas"),
      rect = canvas.getBoundingClientRect(),
      dpr = Math.min(devicePixelRatio || 1, 2);
    if (!rect.width || !rect.height) return;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);
    const atoms = atomsOf(state.molecule),
      coordinates = atoms.map(xyz),
      center = [0, 1, 2].map(
        (k) => coordinates.reduce((s, p) => s + p[k], 0) / coordinates.length,
      );
    const points = coordinates.map((p) => p.map((v, k) => v - center[k]));
    const rotated = points.map(([x, y, z]) => {
      const xx = x * Math.cos(state.ry) + z * Math.sin(state.ry),
        zz = -x * Math.sin(state.ry) + z * Math.cos(state.ry);
      return [
        xx,
        y * Math.cos(state.rx) - zz * Math.sin(state.rx),
        y * Math.sin(state.rx) + zz * Math.cos(state.rx),
      ];
    });
    const radius = Math.max(...points.map((p) => Math.hypot(...p)), 1),
      scale = Math.min(rect.width * 0.42, rect.height * 0.37) / radius;
    const projected = rotated.map(([x, y, z]) => ({
      x: rect.width / 2 + x * scale,
      y: rect.height / 2 + y * scale,
      z,
    }));
    const indexMap = new Map(atoms.map((a, i) => [atomIndex(a, i), i]));
    const items = [];
    bondsOf(state.molecule).forEach((b) => {
      const ai = indexMap.get(Number(b.begin ?? b.start ?? b.atom1 ?? b[0])),
        bi = indexMap.get(Number(b.end ?? b.atom2 ?? b[1]));
      if (ai === undefined || bi === undefined) return;
      items.push({
        kind: "bond",
        a: ai,
        b: bi,
        order: Number(b.order ?? b.bond_order ?? b[2] ?? 1),
        z: (projected[ai].z + projected[bi].z) / 2,
      });
    });
    atoms.forEach((a, i) =>
      items.push({ kind: "atom", a: i, z: projected[i].z }),
    );
    items.sort((a, b) => a.z - b.z);
    const colors = {
      C: "#48614a",
      O: "#b44d4f",
      P: "#b88934",
      H: "#f3f3ed",
      N: "#4f70a0",
    };
    for (const item of items) {
      if (item.kind === "bond") {
        const p = projected[item.a],
          q = projected[item.b],
          dx = q.x - p.x,
          dy = q.y - p.y,
          length = Math.hypot(dx, dy) || 1,
          offset = item.order >= 2 ? 2 : 0;
        ctx.lineCap = "round";
        ctx.strokeStyle = "#8e9b89";
        ctx.lineWidth = 3;
        for (const side of offset ? [-1, 1] : [0]) {
          ctx.beginPath();
          ctx.moveTo(
            p.x - ((side * dy) / length) * offset,
            p.y + ((side * dx) / length) * offset,
          );
          ctx.lineTo(
            q.x - ((side * dy) / length) * offset,
            q.y + ((side * dx) / length) * offset,
          );
          ctx.stroke();
        }
      } else {
        const a = atoms[item.a],
          p = projected[item.a],
          s = symbol(a),
          r = s === "H" ? 3.5 : 7.5,
          selected = state.atom === atomIndex(a, item.a);
        if (selected) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, r + 5, 0, Math.PI * 2);
          ctx.fillStyle = "#e8a16a77";
          ctx.fill();
          ctx.strokeStyle = "#9a541e";
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }
        const grad = ctx.createRadialGradient(p.x - 2, p.y - 3, 1, p.x, p.y, r);
        grad.addColorStop(0, s === "H" ? "#fff" : "#a4b59d");
        grad.addColorStop(1, colors[s] || "#707b76");
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
        ctx.strokeStyle = "#28402e33";
        ctx.lineWidth = 0.5;
        ctx.stroke();
        if (s !== "C" && s !== "H") {
          ctx.fillStyle = "#fff";
          ctx.font = "bold 8px Arial";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(s, p.x, p.y);
        }
      }
    }
  }
  $("view-2d").addEventListener("click", () => setMode("2d"));
  $("view-3d").addEventListener("click", () => setMode("3d"));
  $("clear-atom").addEventListener("click", () => selectAtom(null));
  for (const [id, key] of [
    ["rotation-x", "rx"],
    ["rotation-y", "ry"],
  ])
    $(id).addEventListener("input", (e) => {
      state[key] = (Number(e.target.value) * Math.PI) / 180;
      draw3D();
    });
  $("reset-view").addEventListener("click", () => {
    state.rx = 0.31;
    state.ry = -0.44;
    $("rotation-x").value = 18;
    $("rotation-y").value = -25;
    draw3D();
  });
  let drag = null;
  const canvas = $("molecule-canvas");
  canvas.addEventListener("pointerdown", (e) => {
    drag = [e.clientX, e.clientY];
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!drag) return;
    state.ry += (e.clientX - drag[0]) * 0.012;
    state.rx += (e.clientY - drag[1]) * 0.012;
    state.ry =
      ((((state.ry + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) -
      Math.PI;
    state.rx =
      ((((state.rx + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) -
      Math.PI;
    drag = [e.clientX, e.clientY];
    $("rotation-x").value = (state.rx * 180) / Math.PI;
    $("rotation-y").value = (state.ry * 180) / Math.PI;
    draw3D();
  });
  canvas.addEventListener("pointerup", () => {
    drag = null;
  });
  canvas.addEventListener("pointercancel", () => {
    drag = null;
  });
  window.addEventListener("resize", () => requestAnimationFrame(draw3D));
  $("molecule-list").innerHTML = molecules
    .map((m, i) => {
      const id = moleculeId(m);
      return `<button type="button" class="molecule-choice" data-id="${esc(id)}" aria-pressed="false"><span class="choice-index">${String(i + 1).padStart(2, "0")} / ${esc(knownRoles[id]?.[0] || "MOLECULE")}</span><span class="choice-name">${esc(m.short_name || m.name)}</span><span class="choice-subtitle">${esc(m.subtitle || knownRoles[id]?.[1] || m.formula || "")}</span><span class="choice-arrow arrow" aria-hidden="true"></span></button>`;
    })
    .join("");
  $("molecule-list")
    .querySelectorAll("button")
    .forEach((b) =>
      b.addEventListener("click", () => chooseMolecule(b.dataset.id)),
    );
  $("reaction-cards").innerHTML = reactions
    .map((r, i) => {
      const productId = String(r.product_id || r.product || "").toLowerCase(),
        m = molecules.find((m) => moleculeId(m) === productId),
        steps = r.steps || [];
      return `<article class="reaction-card ${productId.includes("linalool") ? "violet-route" : ""}"><p class="route-kicker">ROUTE ${String(i + 1).padStart(2, "0")} · ${esc(r.enzyme_name || enzymes.find((e) => e.id === r.enzyme_id)?.name || "CHARACTERIZED ACTIVITY")}</p><h3>${esc(r.title || m?.name || "Reaction route")}</h3><p class="route-summary">${esc(r.summary || r.description || r.neutral_equation?.text || "")}</p>${steps.map((s, j) => `<details ${j === 0 ? "open" : ""}><summary>${String(j + 1).padStart(2, "0")} &nbsp; ${esc(typeof s === "string" ? `Reaction step ${j + 1}` : s.title || s.name)}</summary><p>${esc(typeof s === "string" ? s : s.text || s.description)}</p></details>`).join("")}<button class="route-link" type="button" data-product="${esc(productId)}">Inspect this product <span class="arrow" aria-hidden="true"></span></button></article>`;
    })
    .join("");
  if (!reactions.length)
    $("reaction-cards").innerHTML =
      '<p class="unavailable">Reaction descriptions are not included in this data export.</p>';
  $("reaction-cards")
    .querySelectorAll("[data-product]")
    .forEach((b) =>
      b.addEventListener("click", () =>
        chooseMolecule(b.dataset.product, true),
      ),
    );
  $("enzyme-cards").innerHTML = enzymes
    .map((e) => {
      const organism =
          typeof e.organism === "object"
            ? e.organism.scientific_name || e.organism.name
            : e.organism,
        sequence = e.sequence || "",
        structure = data.structural_evidence?.records?.find(
          (r) => r.enzyme_id === e.id,
        ),
        accession = e.accession || e.uniprot_id,
        url = safeURL(
          e.url ||
            e.source_url ||
            (accession
              ? `https://www.uniprot.org/uniprotkb/${accession}/entry`
              : ""),
        );
      return `<article class="enzyme-card"><p class="eyebrow">${esc(e.product_name || e.product_id || "CHARACTERIZED ENZYME")}</p><h3>${esc(e.name || e.protein_name || e.id)}</h3><p class="organism">${esc(organism || "Organism not supplied")}</p><div class="enzyme-meta">${accession ? (url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(accession)} <span class="arrow" aria-hidden="true"></span></a>` : `<span>${esc(accession)}</span>`) : ""}${sequence ? `<span>${sequence.length} amino acids</span>` : ""}${e.reviewed === true ? "<span>Reviewed sequence record</span>" : ""}</div>${structure ? `<p class="fine-print">${structure.status === "experimental" ? `Experimental structure: <a href="https://www.rcsb.org/structure/${esc(structure.pdb_id)}" target="_blank" rel="noopener noreferrer">${esc(structure.pdb_id)} <span class="arrow" aria-hidden="true"></span></a>. ${esc(structure.modeled_alpha_carbon_residues)} reference positions have modeled alpha carbons.` : "No experimental structure is included for this enzyme."}</p>` : ""}</article>`;
    })
    .join("");
  const comparison = data.sequence_comparison || data.alignment || {},
    aa =
      comparison.alignment_a ||
      comparison.aligned_a ||
      comparison.sequences?.[0] ||
      "",
    bb =
      comparison.alignment_b ||
      comparison.aligned_b ||
      comparison.sequences?.[1] ||
      "";
  $("alignment-description").textContent =
    comparison.description ||
    comparison.method ||
    "An alignment compares sequence positions; similarity alone does not establish function.";
  const pct = comparison.identity_percent ?? comparison.percent_identity,
    alignedLength =
      comparison.alignment_columns ??
      comparison.alignment_length ??
      (aa && bb && aa.length === bb.length ? aa.length : null);
  $("alignment-metrics").innerHTML =
    (Number.isFinite(pct)
      ? `<div class="alignment-metric"><strong>${Number(pct).toFixed(1)}%</strong><span>Identity in non-gap overlap</span></div>`
      : "") +
    (Number.isFinite(alignedLength)
      ? `<div class="alignment-metric"><strong>${alignedLength}</strong><span>Alignment columns</span></div>`
      : "");
  if (aa && bb && aa.length === bb.length) {
    let out = "";
    const names = [
      comparison.name_a ||
        enzymes[0]?.short_name ||
        enzymes[0]?.accession ||
        enzymes[0]?.name ||
        "Sequence A",
      comparison.name_b ||
        enzymes[1]?.short_name ||
        enzymes[1]?.accession ||
        enzymes[1]?.name ||
        "Sequence B",
    ];
    for (let start = 0; start < aa.length; start += 50) {
      out += '<div class="alignment-block">';
      for (let row = 0; row < 2; row++) {
        const seq = row ? bb : aa;
        out += `<div class="sequence-row"><span class="sequence-label" title="${esc(names[row])}">${esc(names[row])}</span><span class="sequence-position" title="Alignment column">col ${start + 1}</span><span class="residues">`;
        for (let i = start; i < Math.min(start + 50, aa.length); i++) {
          const cls =
            aa[i] === "-" || bb[i] === "-"
              ? "gap"
              : aa[i] === bb[i]
                ? "match"
                : "different";
          out += `<span class="residue ${cls}">${esc(seq[i])}</span>`;
        }
        out += "</span></div>";
      }
      out += "</div>";
    }
    $("sequence-alignment").innerHTML = out;
  } else {
    $("sequence-alignment").innerHTML =
      '<p class="unavailable">A paired alignment is not available in this export. Open the sequence records above to inspect the source proteins.</p>';
  }
  const notes =
    comparison.notes ||
    comparison.limitations ||
    "Sequence similarity is descriptive. This comparison does not predict substrate choice, product selectivity, or catalytic performance.";
  $("alignment-notes").textContent =
    (Array.isArray(notes) ? notes.join(" ") : notes) +
    " Column numbers refer to alignment positions, not protein residue numbering.";
  $("reaction-scope").textContent =
    data.chemistry?.protonation_note ||
    "The step descriptions are teaching summaries. The evidence panel distinguishes measured activity from proposed mechanistic detail.";
  const sourceList = [
    ...entries(data.sources || data.evidence),
    ...enzymes.flatMap((e) =>
      entries(e.evidence || e.sources).map((s) => ({
        ...s,
        label: s.label || s.title || e.name,
      })),
    ),
    ...entries(data.chemistry?.sources).map((s) => ({
      ...s,
      label: s.label || s.title || `PubChem · ${s.name || s.id}`,
      url: s.url || s.record_url,
      text:
        s.note ||
        s.scope ||
        "Compound identity and stereochemistry used in the curated molecular representation.",
    })),
  ];
  const seen = new Set();
  const sources = sourceList.filter((s) => {
    const key = s.url || s.doi || s.label || s.title;
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  $("evidence-list").innerHTML = sources
    .map((s, i) => {
      const url = safeURL(s.url || (s.doi ? `https://doi.org/${s.doi}` : "")),
        title = s.label || s.title || s.name || "Source record";
      return `<article class="evidence-item"><span class="evidence-number">${String(i + 1).padStart(2, "0")}</span><div><h3>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(title)} <span class="arrow" aria-hidden="true"></span></a>` : esc(title)}</h3><p>${esc(s.text || s.description || s.supports || s.note || "Consult the linked source for its methods and evidence scope.")}</p></div></article>`;
    })
    .join("");
  if (!sources.length)
    $("evidence-list").innerHTML =
      '<p class="unavailable">Source details are available in the repository documentation.</p>';
  if (molecules.length) chooseMolecule(moleculeId(molecules[0]));
  else {
    $("data-error").hidden = false;
    $("molecule-name").textContent = "No molecular structures supplied";
  }
})();
