Project Description
You will create the BikeTourPlus application for a small start-up company. BikeTourPlus is intended to be
used by local bike tour organizers to manage bike tours including participants and to book biking guides,
gear, and biking lodges for any bike tour.
The BikeTourPlus application has a built-in user account for the manager of the local bike tour organizer
called manager@btp.com. Initially, the password for this account is set to manager, but this can be
changed later on. Only the manager may define the start and end date of the biking season. Each year,
there are only a certain number of weeks which allow for safe biking. Each year, these biking weeks are
numbered starting with 1 and the participants are assigned their tour weeks using these numbers (i.e.,
either earlier or later in the biking season).
The manager also specifies the gear available for rent (e.g., regular bike, e-bike, helmet, etc.). Since there
is always enough gear available for all participants, the exact inventory is not tracked for any gear by
BikeTourPlus. Furthermore, the manager defines named combos, i.e., sets of commonly needed gear (at
least two different kinds of gear), which can be rented with a percentage discount if a biking lodge is also
rented. If a lodge is not rented, a combo is rented at the regular price per week (i.e., the sum of the
individual prices of the gear in the combo). Last but not least, the manager also enters the information
about biking lodges (name, address, and class from one to five stars), which are assigned to any
participant wishing to stay the day before and after their bike tour. All participants of a bike tour that
requested a lodge stay at the same lodge.
Each biking guide registers in the system, providing their email address, name, and emergency contact
(i.e., a phone number). The email address is used as the account name, which together with the guide’s
password identifies the guide in the system. Once entered, the email address cannot be changed. Each
biking guide commits to being available for the whole biking season. The weekly cost of a biking guide is
the same for all guides and specified by the manager.
When a participant registers in the system, they also provide an email address, name, and emergency
contact. As is the case for biking guides, the email address is used as the account name and cannot be
changed. The account name and password identify each participant. A participant then indicates for how
many weeks they wish to go on a bike tour and their availability during the biking season (from a start
week to an end week). As the bike tours are very popular, a participant is only allowed to register for one
bike tour per biking season. In addition, a participant selects any gear and/or combos they may wish to
rent (e.g., one e-bike, two bike bags, two combos #1) and indicates whether they want to stay at the
biking lodge before and after their biking tour. The participant is then shown the total cost for the biking
tour which includes the cost of the biking guide and the cost of the gear. The biking lodge stay is provided
free of charge. Note that the prices of items do not have any cents.
At some point before the start of the biking season, the manager initiates the creation of each bike tour
including its guide, its participants, its biking weeks, and its biking lodge, so that the start and end week
as well as the total costs for the bike tour can be shown to each participant of the bike tour. Each bike
tour is assigned one biking guide.
The participant then has to pay the total cost for their bike tour. The actual payment is handled outside
the BikeTourPlus application, i.e., only the authorization code for the payment needs to be entered into
the application. If a participant has to cancel, a certain percentage of the total cost is refunded, which
needs to be noted in the participant’s file. More information about the bike tour creation process will be
provided at a later point. At the end of the biking season, all participants and guides are removed from
the BikeTourPlus application.