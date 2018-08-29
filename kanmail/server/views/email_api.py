from flask import jsonify, make_response, request

from kanmail.server.app import app
from kanmail.server.mail import (
    copy_folder_emails,
    get_all_folders,
    get_folder_email_part,
    get_folder_email_texts,
    get_folder_emails,
    move_folder_emails,
    star_folder_emails,
    sync_folder_emails,
    unstar_folder_emails,
)
from kanmail.server.util import get_list_or_400, get_or_400


@app.route('/api/folders', methods=['GET'])
def api_get_folders():
    '''
    List available folders/mailboxes for all the accounts.
    '''

    folders, meta = get_all_folders()

    return jsonify(folders=folders, folder_meta=meta)


@app.route('/api/emails/<account>/<folder>', methods=['GET'])
def api_get_account_folder_emails(account, folder):
    '''
    Get (more) emails for a folder in a given account.
    '''

    batch_size = None

    try:
        batch_size = int(request.args.get('batch_size'))
    except (TypeError, ValueError):
        pass

    emails, meta = get_folder_emails(
        account, folder,
        query=request.args.get('query'),
        reset=request.args.get('reset') == 'true',
        batch_size=batch_size,
    )

    return jsonify(emails=emails, meta=meta)


@app.route('/api/emails/<account>/<folder>/sync', methods=['GET'])
def api_sync_account_folder_emails(account, folder):
    '''
    Sync emails within a folder for a given account.
    '''

    new_emails, deleted_uids, meta = sync_folder_emails(
        account, folder,
        query=request.args.get('query'),
    )

    return jsonify(
        new_emails=new_emails,
        deleted_uids=deleted_uids,
        meta=meta,
    )


@app.route('/api/emails/<account>/<folder>/text', methods=['GET'])
def api_get_account_email_texts(account, folder):
    '''
    Get a specific list of email texts by UID for a given account/folder.
    '''

    uids = get_list_or_400(request.args, 'uid', type=int)

    emails = get_folder_email_texts(account, folder, uids)

    return jsonify(emails=emails)


@app.route('/api/emails/<account>/<folder>/<int:uid>/<part_number>')
def api_get_account_email_part(account, folder, uid, part_number):
    '''
    Get a specific part (attachment) of a single email by account/folder/UID.
    '''

    mime_type, data = get_folder_email_part(account, folder, uid, part_number)

    if mime_type is None:
        response = jsonify(error='Could not find part: {0}'.format(part_number))
        response.status_code = 404
        return response

    response = make_response(data)
    response.headers['Content-Type'] = mime_type

    return response


@app.route('/api/emails/<account>/<folder>/move', methods=['POST'])
def api_move_account_emails(account, folder):
    '''
    Move emails from one folder to another within a given account.
    '''

    request_data = request.get_json()
    message_uids = get_or_400(request_data, 'message_uids')
    new_folder = get_or_400(request_data, 'new_folder')

    move_folder_emails(account, folder, message_uids, new_folder)

    return jsonify(moved=True)


@app.route('/api/emails/<account>/<folder>/copy', methods=['POST'])
def api_copy_account_emails(account, folder):
    '''
    Copy emails from one folder to another within a given account.
    '''

    request_data = request.get_json()
    message_uids = get_or_400(request_data, 'message_uids')
    new_folder = get_or_400(request_data, 'new_folder')

    copy_folder_emails(account, folder, message_uids, new_folder)

    return jsonify(copied=True)


# @app.route('/api/emails/<account>/<folder>/delete', methods=['POST'])
# def api_delete_account_emails(account, folder):
#     '''
#     Delete emails from a folder in a given account.
#     '''

#     from time import sleep
#     from flask import abort

#     sleep(5)
#     abort(500)

#     request_data = request.get_json()
#     message_uids = get_or_400(request_data, 'message_uids')

#     delete_folder_emails(account, folder, message_uids)

#     return jsonify(deleted=True)


@app.route('/api/emails/<account>/<folder>/star', methods=['POST'])
def api_star_account_emails(account, folder):
    '''
    Star emails in a given account/folder.
    '''

    request_data = request.get_json()
    message_uids = get_or_400(request_data, 'message_uids')

    star_folder_emails(account, folder, message_uids)

    return jsonify(starred=True)


@app.route('/api/emails/<account>/<folder>/unstar', methods=['POST'])
def api_unstar_account_emails(account, folder):
    '''
    Unstar emails in a given account/folder.
    '''

    request_data = request.get_json()
    message_uids = get_or_400(request_data, 'message_uids')

    unstar_folder_emails(account, folder, message_uids)

    return jsonify(unstarred=True)


@app.route('/api/emails/<account>', methods=['POST'])
def api_send_account_email():
    '''
    Create (send) emails from one of the accounts.
    '''