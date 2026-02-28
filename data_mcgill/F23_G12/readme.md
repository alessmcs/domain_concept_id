Project Description
You will create the AssetPlus application for a hotel in the Montreal area. AssetPlus is intended to be
used by hotel staff to effectively manage hotel assets such as furniture and appliances in rooms and
hallways of a hotel as well as maintenance tasks.
The AssetPlus application has a built-in user account for the manager of the hotel called
manager@ap.com. Initially, the password for this account is set to manager, but this can be changed
later on by the person with manager access. Each employee selects a company email address, which is
required to end with the domain name @ap.com. The email address is used as the account name, which
together with the employee’s password identifies the employee in the system. When a guest registers in
the system, they also provide an email address as the account name and a password. The account name
and password identify each guest. Once entered, the email address of a guest or employee cannot be
changed. Optionally, each user, including the manager, can include their name and phone number.
The manager specifies the assets available in the hotel. For example, a hotel contains multiple lamps,
located on multiple floors and rooms within the hotel. When adding an asset to the AssetPlus
application, the purchase date, expected lifespan, and location within the hotel (floor and room number
as required) is noted. Furthermore, a unique asset number is assigned to the asset.
The AssetPlus application keeps track of the maintenance history for every asset within the hotel. The
manager, guests, and employees have the ability to open a maintenance ticket, by including a description
of the request and linking it with a specific asset, if applicable. For example, a maintenance ticket can be
opened for a defective lamp located at a specific floor and room number within the hotel. Optionally,
users can provide one or more image URL links to support their maintenance request.
Once a ticket is open, users can track the progress of the maintenance tickets they have raised by
providing the ticket number. The manager is responsible for reviewing open tickets and assigning them to
maintenance staff for further action. Both managers and employees can be assigned maintenance tasks.
The manager also defines the priority level and a time estimate for the ticket. A ticket can be urgent,
meaning work for it must start within two days from the day it was raised; normal, meaning work must
start within a week; and low, meaning work must start within three weeks. The time estimate specifies
the time range allocated from the time maintenance staff starts working on the ticket until it is resolved.
The time estimate ranges are less than a day, 1-3 days, 3-7 days, 1-3 weeks, and 3+ weeks.
Furthermore, the manager specifies whether or not a maintenance ticket will require manager approval
once the ticket is resolved, such that it can be closed. Maintenance notes can be written by the manager
and hotel employees to document the ticket’s progress on a date. Once a fix is complete, the
maintenance staff marks the maintenance ticket as resolved. Then, if the manager’s approval is required,
the manager can either approve the fix, which marks the ticket as closed, or not approve the fix, in which
case the ticket is returned to the maintenance staff with a note explaining the further action to be taken.
On the other hand, if the manager's approval is not required, a ticket is automatically closed.