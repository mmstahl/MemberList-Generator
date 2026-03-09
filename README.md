# Membership List Update Guide

Follow these steps to export user data, process it via scripts, and update the membership list on the WordPress site.

## 1. Export Member Data
1. Log in to the WordPress site as an **Administrator**.
2. Navigate to **Dashboard** -> **Users** -> **All Users**.
3. Export the members' data using the following specific fields:

> `user_email`, `first_name`, `last_name`, `partnerfirst`, `partnerlast`, `partneremail`, `cellphone1`, `partnerphone`, `homephone`, `home_address`, `yourgender`, `partnergender`, `contact_list_privacy_setting`, `privacy_approval`

4. Save this file as `members data raw.csv`.

## 2. Process the Data
Run the local Python scripts to format the data and generate the final document:

1. **Run Pre-processing:** Execute `pre_process.py`. This will generate `pre-processing output.csv`.
2. **Generate PDF:** Execute `MemberList Generator.py`. This will generate the final file: `members_list_2026.pdf`.

## 3. Upload to WordPress

### Initial Upload
If this is the **first time** the file is being added, simply upload `members_list_2026.pdf` to the WordPress **Media Library**.

### Updating Existing File (SFTP)
WordPress will not automatically overwrite existing media files. To update the list, you must use **FileZilla** (or another SFTP client):

* **Host:** `sftp://kehilatyedidya.wordpress.com@sftp.wp.com`
* **Path:** `/srv/htdocs/wp-content/uploads`
* **Action:** Transfer the new file to this directory. When prompted that the file already exists, select **Overwrite**.

## 4. Update the Page Content (one-time thing)
Once the file is uploaded, you need to link it to the live page:

1. Browse to the **Membership List** page (found under the *Members Info* menu) while logged in as an administrator.
2. Select **Edit Page**.
3. Add a **File Block**.
4. Choose the file from the **Media Library** (ensure you select the newly uploaded version).
5. **Important:** Repeat these steps for the **Hebrew** version of the site to ensure both languages are updated.
