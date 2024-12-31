from .models import Session, Signup


def collect_signups(session_id: int):
    session = Session.objects.get(id=session_id)
    signups = Signup.objects.filter(session=session).order_by(
        "waiting_list__date_added"
    )
    print(signups)


if __name__ == "__main__":
    collect_signups(2)
