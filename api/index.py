import os
from io import BytesIO
from flask import Flask, jsonify, redirect, render_template, request, send_file
import qrcode
from supabase import Client, create_client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Defina SUPABASE_URL e SUPABASE_ANON_KEY nas variaveis de ambiente.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin: Client | None = (
    create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_SERVICE_ROLE_KEY else None
)


def _get_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.replace("Bearer ", "", 1).strip()


@app.route("/")
def home():
    return redirect("/login-view")


@app.route("/login-view")
def login_view():
    return render_template("login.html")


@app.route("/dashboard-view")
def dashboard_view():
    return render_template("dashboard.html")


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Campos obrigatorios: email e password"}), 400

    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        user_id = getattr(getattr(res, "user", None), "id", None)
        return jsonify({"message": "Usuario criado com sucesso", "id": user_id}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Campos obrigatorios: email e password"}), 400

    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        access_token = getattr(getattr(res, "session", None), "access_token", None)
        if not access_token:
            return jsonify({"error": "Nao foi possivel gerar token de acesso"}), 401
        return jsonify({"access_token": access_token})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 401


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    token = _get_bearer_token()
    if not token:
        return jsonify({"error": "Token ausente ou invalido"}), 401

    data = request.get_json(silent=True) or {}
    slug = data.get("slug")
    conteudo = data.get("conteudo")
    if not slug or not conteudo:
        return jsonify({"error": "Campos obrigatorios: slug e conteudo"}), 400

    try:
        supabase.postgrest.auth(token)
        user = supabase.auth.get_user(token)
        user_id = getattr(getattr(user, "user", None), "id", None)
        if not user_id:
            return jsonify({"error": "Usuario invalido"}), 401

        res = (
            supabase.table("qrcodes")
            .insert(
                {
                    "slug": slug,
                    "conteudo_original": conteudo,
                    "user_id": user_id,
                }
            )
            .execute()
        )
        return jsonify(res.data), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/dashboard", methods=["GET"])
def dashboard():
    token = _get_bearer_token()
    if not token:
        return jsonify({"error": "Token ausente ou invalido"}), 401

    try:
        supabase.postgrest.auth(token)
        res = supabase.table("qrcodes").select("*").order("created_at", desc=True).execute()
        return jsonify(res.data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/qrcode/<slug>", methods=["PATCH"])
def editar_slug(slug: str):
    token = _get_bearer_token()
    if not token:
        return jsonify({"error": "Token ausente ou invalido"}), 401

    data = request.get_json(silent=True) or {}
    novo_slug = data.get("novo_slug")
    if not novo_slug:
        return jsonify({"error": "Campo obrigatorio: novo_slug"}), 400

    try:
        supabase.postgrest.auth(token)
        res = (
            supabase.table("qrcodes")
            .update({"slug": novo_slug})
            .eq("slug", slug)
            .execute()
        )
        if not res.data:
            return jsonify({"error": "QR Code nao encontrado"}), 404
        return jsonify(res.data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/qrcode/<slug>", methods=["DELETE"])
def excluir_qrcode(slug: str):
    token = _get_bearer_token()
    if not token:
        return jsonify({"error": "Token ausente ou invalido"}), 401

    try:
        supabase.postgrest.auth(token)
        res = supabase.table("qrcodes").delete().eq("slug", slug).execute()
        if not res.data:
            return jsonify({"error": "QR Code nao encontrado"}), 404
        return jsonify({"message": "QR Code excluido com sucesso"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/l/<slug>", methods=["GET"])
def ler_qr(slug: str):
    try:
        db_client = supabase_admin or supabase
        response = db_client.table("qrcodes").select("*").eq("slug", slug).limit(1).execute()
        if not response.data:
            return "QR Code invalido", 404

        item = response.data[0]
        novo_contador = int(item.get("contador", 0)) + 1
        db_client.table("qrcodes").update({"contador": novo_contador}).eq("slug", slug).execute()
        return redirect(item["conteudo_original"])
    except Exception:
        return "Erro ao processar QR Code", 500


@app.route("/qr/<slug>.png", methods=["GET"])
def gerar_qr(slug: str):
    try:
        db_client = supabase_admin or supabase
        response = db_client.table("qrcodes").select("slug").eq("slug", slug).limit(1).execute()
        if not response.data:
            return "QR Code invalido", 404

        link_rastreavel = request.url_root.rstrip("/") + f"/l/{slug}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(link_rastreavel)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        img_io = BytesIO()
        img.save(img_io, "PNG")
        img_io.seek(0)

        return send_file(
            img_io,
            mimetype="image/png",
            as_attachment=True,
            download_name=f"qrcode-{slug}.png",
        )
    except Exception:
        return "Erro ao gerar QR Code", 500
